from pathlib import Path
import csv
import json

import matplotlib.pyplot as plt
import numpy as np


# ============================================================
# CONFIG
# ============================================================

# Directory containing the individual tournament folders.
#
# Expected example:
#
# BotExperiments/
# ├── aggregate_results.py
# └── results/
#     ├── tournament_run_1/
#     │   └── games.csv
#     ├── tournament_run_2/
#     │   └── games.csv
#     ├── tournament_run_3/
#     │   └── games.csv
#     ├── tournament_run_4/
#     │   └── games.csv
#     └── tournament_run_5/
#         └── games.csv

SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_ROOT = SCRIPT_DIR / "results"

# Combined results will be saved here.
OUTPUT_DIR = RESULTS_ROOT / "combined_statistics"

# Optional:
# Set this to a list of folder names when you only want specific runs.
#
# Example:
# TOURNAMENT_FOLDERS = [
#     "main_tournament_run_1",
#     "main_tournament_run_2",
#     "main_tournament_run_3",
#     "main_tournament_run_4",
#     "main_tournament_run_5",
# ]
#
# Leave as None to automatically read every games.csv under RESULTS_ROOT.
TOURNAMENT_FOLDERS = None


# ============================================================
# LOADING
# ============================================================

def find_games_files():
    """
    Find all games.csv files that should be included.
    """

    if TOURNAMENT_FOLDERS is not None:
        paths = []

        for folder_name in TOURNAMENT_FOLDERS:
            path = RESULTS_ROOT / folder_name / "games.csv"

            if path.exists():
                paths.append(path)
            else:
                print(f"Warning: file does not exist: {path}")

        return paths

    # Automatically find all games.csv files recursively.
    paths = list(RESULTS_ROOT.rglob("games.csv"))

    # Do not load our own combined output again.
    paths = [
        path for path in paths
        if OUTPUT_DIR not in path.parents
    ]

    return sorted(paths)


def load_games_csv(path):
    """
    Load one games.csv file and convert numeric columns
    to the correct Python data types.
    """

    rows = []

    with open(path, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        required_columns = {
            "bot_a",
            "bot_b",
            "winner",
            "num_moves",
            "time",
        }

        if reader.fieldnames is None:
            print(f"Warning: empty CSV file: {path}")
            return rows

        missing_columns = required_columns - set(reader.fieldnames)

        if missing_columns:
            print(
                f"Warning: skipping {path}. "
                f"Missing columns: {sorted(missing_columns)}"
            )
            return rows

        for row in reader:
            try:
                parsed_row = dict(row)

                parsed_row["game_index"] = int(
                    row.get("game_index", len(rows))
                )

                parsed_row["swapped"] = str(
                    row.get("swapped", "False")
                ).lower() in ("true", "1", "yes")

                parsed_row["winner_raw"] = int(
                    row.get("winner_raw", 0)
                )

                parsed_row["num_moves"] = int(row["num_moves"])
                parsed_row["time"] = float(row["time"])

                # Store where this game came from.
                parsed_row["source_run"] = path.parent.name

                rows.append(parsed_row)

            except (ValueError, TypeError) as error:
                print(
                    f"Warning: skipping invalid row in {path}: "
                    f"{error}"
                )

    return rows


def load_all_games(paths):
    all_games = []

    for path in paths:
        games = load_games_csv(path)
        all_games.extend(games)

        print(
            f"Loaded {len(games):5d} games from "
            f"{path.parent.name}"
        )

    return all_games


# ============================================================
# SAVING
# ============================================================

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def save_combined_csv(path, rows):
    if not rows:
        return

    fieldnames = [
        "source_run",
        "game_key",
        "bot_a",
        "bot_b",
        "game_index",
        "swapped",
        "winner",
        "winner_raw",
        "num_moves",
        "time",
    ]

    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )

        writer.writeheader()
        writer.writerows(rows)


# ============================================================
# SUMMARY
# ============================================================

def get_bot_names(all_games):
    names = set()

    for game in all_games:
        names.add(game["bot_a"])
        names.add(game["bot_b"])

    return sorted(names)


def get_pair_games(all_games, bot_a, bot_b):
    return [
        game
        for game in all_games
        if {game["bot_a"], game["bot_b"]} == {bot_a, bot_b}
    ]


def summarize_pairwise(all_games, bot_names):
    """
    Create statistics for each bot against each opponent.
    """

    summary = {}

    for bot_a in bot_names:
        summary[bot_a] = {}

        for bot_b in bot_names:
            if bot_a == bot_b:
                continue

            games = get_pair_games(all_games, bot_a, bot_b)

            if not games:
                continue

            wins = sum(
                1 for game in games
                if game["winner"] == bot_a
            )

            losses = sum(
                1 for game in games
                if game["winner"] == bot_b
            )

            draws = sum(
                1 for game in games
                if game["winner"] == "draw"
            )

            total_games = len(games)

            summary[bot_a][bot_b] = {
                "wins": wins,
                "losses": losses,
                "draws": draws,
                "games": total_games,
                "win_rate": wins / total_games,
                "loss_rate": losses / total_games,
                "draw_rate": draws / total_games,
                "score": wins + 0.5 * draws,
                "score_rate": (
                    wins + 0.5 * draws
                ) / total_games,
                "avg_moves": sum(
                    game["num_moves"] for game in games
                ) / total_games,
                "avg_time": sum(
                    game["time"] for game in games
                ) / total_games,
            }

    return summary


def summarize_overall(all_games, bot_names):
    """
    Create overall statistics for every bot across all opponents.
    """

    overall = {}

    for bot in bot_names:
        games = [
            game for game in all_games
            if bot in (game["bot_a"], game["bot_b"])
        ]

        wins = sum(
            1 for game in games
            if game["winner"] == bot
        )

        losses = sum(
            1 for game in games
            if game["winner"] not in (bot, "draw")
        )

        draws = sum(
            1 for game in games
            if game["winner"] == "draw"
        )

        total_games = len(games)

        if total_games == 0:
            continue

        score = wins + 0.5 * draws

        overall[bot] = {
            "wins": wins,
            "losses": losses,
            "draws": draws,
            "games": total_games,
            "win_rate": wins / total_games,
            "loss_rate": losses / total_games,
            "draw_rate": draws / total_games,
            "score": score,
            "score_rate": score / total_games,
            "avg_moves": sum(
                game["num_moves"] for game in games
            ) / total_games,
            "avg_time": sum(
                game["time"] for game in games
            ) / total_games,
        }

    return overall


def create_full_summary(all_games, bot_names, source_files):
    return {
        "number_of_runs": len(source_files),
        "total_games": len(all_games),
        "bots": bot_names,
        "source_files": [str(path) for path in source_files],
        "overall": summarize_overall(all_games, bot_names),
        "pairwise": summarize_pairwise(all_games, bot_names),
    }


# ============================================================
# PLOT HELPERS
# ============================================================

def add_bar_labels(ax, values, decimals=1):
    for index, value in enumerate(values):
        ax.text(
            index,
            value,
            f"{value:.{decimals}f}",
            ha="center",
            va="bottom",
        )


# ============================================================
# WIN-RATE HEATMAP
# ============================================================

def plot_winrate_heatmap(pairwise_summary, bot_names, out_path):
    matrix = np.full(
        (len(bot_names), len(bot_names)),
        np.nan,
    )

    for row, bot in enumerate(bot_names):
        for column, opponent in enumerate(bot_names):
            if bot == opponent:
                continue

            if opponent in pairwise_summary.get(bot, {}):
                win_rate = pairwise_summary[bot][opponent]["win_rate"]
                matrix[row, column] = win_rate * 100

    fig, ax = plt.subplots(figsize=(10, 8))

    image = ax.imshow(
        matrix,
        vmin=0,
        vmax=100,
    )

    ax.set_xticks(range(len(bot_names)))
    ax.set_yticks(range(len(bot_names)))

    ax.set_xticklabels(
        bot_names,
        rotation=35,
        ha="right",
    )

    ax.set_yticklabels(bot_names)

    ax.set_title("Combined win-rate heatmap")
    ax.set_xlabel("Opponent")
    ax.set_ylabel("Bot")

    for row in range(len(bot_names)):
        for column in range(len(bot_names)):
            if row == column:
                text = "-"
            elif np.isnan(matrix[row, column]):
                text = "N/A"
            else:
                text = f"{matrix[row, column]:.1f}%"

            ax.text(
                column,
                row,
                text,
                ha="center",
                va="center",
            )

    fig.colorbar(
        image,
        ax=ax,
        label="Win rate (%)",
    )

    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


# ============================================================
# TOURNAMENT SCORE
# ============================================================

def plot_total_scores(overall_summary, bot_names, out_path):
    scores = [
        overall_summary[bot]["score"]
        for bot in bot_names
    ]

    fig, ax = plt.subplots(figsize=(11, 6))

    ax.bar(bot_names, scores)

    ax.set_title("Combined tournament score")
    ax.set_ylabel("Points: win = 1, draw = 0.5")
    ax.set_xlabel("Bot")

    ax.tick_params(
        axis="x",
        labelrotation=35,
    )

    add_bar_labels(ax, scores, decimals=1)

    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


# ============================================================
# SCORE RATE
# ============================================================

def plot_score_rates(overall_summary, bot_names, out_path):
    score_rates = [
        overall_summary[bot]["score_rate"] * 100
        for bot in bot_names
    ]

    fig, ax = plt.subplots(figsize=(11, 6))

    ax.bar(bot_names, score_rates)

    ax.set_title("Combined score rate")
    ax.set_ylabel("Score rate (%)")
    ax.set_xlabel("Bot")
    ax.set_ylim(0, 100)

    ax.tick_params(
        axis="x",
        labelrotation=35,
    )

    add_bar_labels(ax, score_rates, decimals=1)

    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


# ============================================================
# AVERAGE GAME LENGTH
# ============================================================

def plot_avg_moves(overall_summary, bot_names, out_path):
    avg_moves = [
        overall_summary[bot]["avg_moves"]
        for bot in bot_names
    ]

    fig, ax = plt.subplots(figsize=(11, 6))

    ax.bar(bot_names, avg_moves)

    ax.set_title("Combined average game length")
    ax.set_ylabel("Average number of moves")
    ax.set_xlabel("Bot")

    ax.tick_params(
        axis="x",
        labelrotation=35,
    )

    add_bar_labels(ax, avg_moves, decimals=1)

    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


# ============================================================
# AVERAGE GAME TIME
# ============================================================

def plot_avg_time(overall_summary, bot_names, out_path):
    avg_times = [
        overall_summary[bot]["avg_time"]
        for bot in bot_names
    ]

    fig, ax = plt.subplots(figsize=(11, 6))

    ax.bar(bot_names, avg_times)

    ax.set_title("Combined average game time")
    ax.set_ylabel("Average time per game (seconds)")
    ax.set_xlabel("Bot")

    ax.tick_params(
        axis="x",
        labelrotation=35,
    )

    add_bar_labels(ax, avg_times, decimals=2)

    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


# ============================================================
# WINS / LOSSES / DRAWS
# ============================================================

def plot_results_distribution(overall_summary, bot_names, out_path):
    wins = [
        overall_summary[bot]["wins"]
        for bot in bot_names
    ]

    losses = [
        overall_summary[bot]["losses"]
        for bot in bot_names
    ]

    draws = [
        overall_summary[bot]["draws"]
        for bot in bot_names
    ]

    x = np.arange(len(bot_names))
    width = 0.25

    fig, ax = plt.subplots(figsize=(12, 7))

    ax.bar(
        x - width,
        wins,
        width,
        label="Wins",
    )

    ax.bar(
        x,
        losses,
        width,
        label="Losses",
    )

    ax.bar(
        x + width,
        draws,
        width,
        label="Draws",
    )

    ax.set_title("Combined wins, losses and draws")
    ax.set_ylabel("Number of games")
    ax.set_xlabel("Bot")

    ax.set_xticks(x)
    ax.set_xticklabels(
        bot_names,
        rotation=35,
        ha="right",
    )

    ax.legend()

    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


# ============================================================
# WIN / DRAW / LOSS PERCENTAGES
# ============================================================

def plot_result_rates(overall_summary, bot_names, out_path):
    win_rates = [
        overall_summary[bot]["win_rate"] * 100
        for bot in bot_names
    ]

    draw_rates = [
        overall_summary[bot]["draw_rate"] * 100
        for bot in bot_names
    ]

    loss_rates = [
        overall_summary[bot]["loss_rate"] * 100
        for bot in bot_names
    ]

    x = np.arange(len(bot_names))

    fig, ax = plt.subplots(figsize=(12, 7))

    ax.bar(
        x,
        win_rates,
        label="Win rate",
    )

    ax.bar(
        x,
        draw_rates,
        bottom=win_rates,
        label="Draw rate",
    )

    win_plus_draw = [
        win + draw
        for win, draw in zip(win_rates, draw_rates)
    ]

    ax.bar(
        x,
        loss_rates,
        bottom=win_plus_draw,
        label="Loss rate",
    )

    ax.set_title("Combined result percentages")
    ax.set_ylabel("Percentage of games")
    ax.set_xlabel("Bot")
    ax.set_ylim(0, 100)

    ax.set_xticks(x)
    ax.set_xticklabels(
        bot_names,
        rotation=35,
        ha="right",
    )

    ax.legend()

    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


# ============================================================
# GAMES PER RUN
# ============================================================

def plot_games_per_run(all_games, out_path):
    counts = {}

    for game in all_games:
        run_name = game["source_run"]
        counts[run_name] = counts.get(run_name, 0) + 1

    run_names = sorted(counts)
    values = [counts[name] for name in run_names]

    fig, ax = plt.subplots(figsize=(11, 6))

    ax.bar(run_names, values)

    ax.set_title("Number of games loaded from each run")
    ax.set_ylabel("Games")
    ax.set_xlabel("Tournament run")

    ax.tick_params(
        axis="x",
        labelrotation=35,
    )

    add_bar_labels(ax, values, decimals=0)

    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


# ============================================================
# TEXT OUTPUT
# ============================================================

def print_overall_statistics(overall_summary, bot_names):
    ranking = sorted(
        bot_names,
        key=lambda bot: overall_summary[bot]["score_rate"],
        reverse=True,
    )

    print()
    print("=" * 100)
    print("OVERALL RANKING")
    print("=" * 100)

    header = (
        f"{'Rank':<6}"
        f"{'Bot':<25}"
        f"{'Games':>8}"
        f"{'Wins':>8}"
        f"{'Losses':>9}"
        f"{'Draws':>8}"
        f"{'Win %':>10}"
        f"{'Score %':>10}"
        f"{'Avg moves':>12}"
        f"{'Avg time':>12}"
    )

    print(header)
    print("-" * len(header))

    for rank, bot in enumerate(ranking, start=1):
        stats = overall_summary[bot]

        print(
            f"{rank:<6}"
            f"{bot:<25}"
            f"{stats['games']:>8}"
            f"{stats['wins']:>8}"
            f"{stats['losses']:>9}"
            f"{stats['draws']:>8}"
            f"{stats['win_rate'] * 100:>9.2f}%"
            f"{stats['score_rate'] * 100:>9.2f}%"
            f"{stats['avg_moves']:>12.2f}"
            f"{stats['avg_time']:>11.2f}s"
        )


def print_pairwise_statistics(pairwise_summary, bot_names):
    print()
    print("=" * 100)
    print("PAIRWISE STATISTICS")
    print("=" * 100)

    for index, bot_a in enumerate(bot_names):
        for bot_b in bot_names[index + 1:]:
            if bot_b not in pairwise_summary.get(bot_a, {}):
                continue

            stats_a = pairwise_summary[bot_a][bot_b]
            stats_b = pairwise_summary[bot_b][bot_a]

            print()
            print(f"{bot_a} vs {bot_b}")
            print("-" * 60)

            print(
                f"Games: {stats_a['games']}\n"
                f"{bot_a} wins: {stats_a['wins']} "
                f"({stats_a['win_rate'] * 100:.2f}%)\n"
                f"{bot_b} wins: {stats_b['wins']} "
                f"({stats_b['win_rate'] * 100:.2f}%)\n"
                f"Draws: {stats_a['draws']} "
                f"({stats_a['draw_rate'] * 100:.2f}%)\n"
                f"Average moves: {stats_a['avg_moves']:.2f}\n"
                f"Average time: {stats_a['avg_time']:.2f}s"
            )


# ============================================================
# MAIN
# ============================================================

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    games_files = find_games_files()

    if not games_files:
        print(f"No games.csv files found under: {RESULTS_ROOT}")
        return

    print("=" * 100)
    print("FILES TO COMBINE")
    print("=" * 100)

    for path in games_files:
        print(path)

    print()

    all_games = load_all_games(games_files)

    if not all_games:
        print("No valid games were loaded.")
        return

    bot_names = get_bot_names(all_games)

    pairwise_summary = summarize_pairwise(
        all_games,
        bot_names,
    )

    overall_summary = summarize_overall(
        all_games,
        bot_names,
    )

    full_summary = create_full_summary(
        all_games,
        bot_names,
        games_files,
    )

    # Save data.
    save_combined_csv(
        OUTPUT_DIR / "all_games.csv",
        all_games,
    )

    save_json(
        OUTPUT_DIR / "summary.json",
        full_summary,
    )

    # Create plots.
    plot_winrate_heatmap(
        pairwise_summary,
        bot_names,
        OUTPUT_DIR / "winrate_heatmap.png",
    )

    plot_total_scores(
        overall_summary,
        bot_names,
        OUTPUT_DIR / "total_scores.png",
    )

    plot_score_rates(
        overall_summary,
        bot_names,
        OUTPUT_DIR / "score_rates.png",
    )

    plot_avg_moves(
        overall_summary,
        bot_names,
        OUTPUT_DIR / "avg_moves.png",
    )

    plot_avg_time(
        overall_summary,
        bot_names,
        OUTPUT_DIR / "avg_time.png",
    )

    plot_results_distribution(
        overall_summary,
        bot_names,
        OUTPUT_DIR / "wins_losses_draws.png",
    )

    plot_result_rates(
        overall_summary,
        bot_names,
        OUTPUT_DIR / "result_rates.png",
    )

    plot_games_per_run(
        all_games,
        OUTPUT_DIR / "games_per_run.png",
    )

    print_overall_statistics(
        overall_summary,
        bot_names,
    )

    print_pairwise_statistics(
        pairwise_summary,
        bot_names,
    )

    print()
    print("=" * 100)
    print("COMBINED STATISTICS FINISHED")
    print("=" * 100)
    print(f"Runs loaded: {len(games_files)}")
    print(f"Games loaded: {len(all_games)}")
    print(f"Bots found: {', '.join(bot_names)}")
    print(f"Saved to: {OUTPUT_DIR}")
    print()
    print("Created files:")
    print("  all_games.csv")
    print("  summary.json")
    print("  winrate_heatmap.png")
    print("  total_scores.png")
    print("  score_rates.png")
    print("  avg_moves.png")
    print("  avg_time.png")
    print("  wins_losses_draws.png")
    print("  result_rates.png")
    print("  games_per_run.png")


if __name__ == "__main__":
    main()
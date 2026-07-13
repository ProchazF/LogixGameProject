import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LOGIX_ROOT = REPO_ROOT / "EvaluationFunction" / "eval_func_v2"
sys.path.insert(0, str(LOGIX_ROOT))

import json
import csv
import time
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np

from bots import (
    RandomBot,
    HeuristicBot,
    NeuralAlphaBetaBot,
    MCTSBot,
)

from logix_az.env_logix_helper import LogixShapeEnv


# ============================================================
# CONFIG
# ============================================================

GAMES_PER_PAIR = 250
MAX_GAME_LEN = 50

# Keep this the same to resume.
# Change it when you want a completely new tournament.
TOURNAMENT_NAME = "main_tournament_resume_3"

# If True, existing games.csv is loaded and completed games are skipped.
RESUME = True


# ============================================================
# GAME LOGIC
# ============================================================

def play_game(bot_p1, bot_p2, max_game_len=100, seed=None):
    env = LogixShapeEnv(n=7, max_game_len=max_game_len, seed=seed)

    done = False
    result = 0
    moves = []

    start = time.time()

    while not done:
        bot = bot_p1 if env.player == +1 else bot_p2
        player = env.player

        move = bot.choose_move(env)

        if move not in env.legal_moves():
            print(f"Illegal move chosen: {move}, replacing with first legal move")
            move = env.legal_moves()[0]

        _, done, result = env.step(move)

        moves.append({
            "player": player,
            "move": list(move),
        })

    elapsed = time.time() - start

    return {
        "winner": int(result),
        "num_moves": len(moves),
        "time": elapsed,
        "moves": moves,
    }


def game_key(bot_a_name, bot_b_name, game_index):
    return f"{bot_a_name}__VS__{bot_b_name}__GAME__{game_index}"


def run_pair(
    bot_a_name,
    bot_a,
    bot_b_name,
    bot_b,
    games_per_pair,
    max_game_len,
    all_results,
    completed_keys,
    out_dir,
    bot_names,
):
    for i in range(games_per_pair):
        key = game_key(bot_a_name, bot_b_name, i)

        if key in completed_keys:
            print(f"Skipping finished game: {bot_a_name} vs {bot_b_name} {i + 1}/{games_per_pair}")
            continue

        swapped = i % 2 == 1

        if swapped:
            p1_bot = bot_b
            p2_bot = bot_a
        else:
            p1_bot = bot_a
            p2_bot = bot_b

        game = play_game(p1_bot, p2_bot, max_game_len=max_game_len)

        winner = game["winner"]

        if winner == 0:
            winner_name = "draw"
        elif not swapped:
            winner_name = bot_a_name if winner == +1 else bot_b_name
        else:
            winner_name = bot_b_name if winner == +1 else bot_a_name

        row = {
            "game_key": key,
            "bot_a": bot_a_name,
            "bot_b": bot_b_name,
            "game_index": i,
            "swapped": swapped,
            "winner": winner_name,
            "winner_raw": winner,
            "num_moves": game["num_moves"],
            "time": game["time"],
        }

        all_results.append(row)
        completed_keys.add(key)

        save_csv(out_dir / "games.csv", all_results)

        summary = summarize(all_results, bot_names)
        save_json(out_dir / "summary.json", summary)

        print(
            f"{bot_a_name} vs {bot_b_name} "
            f"{i + 1}/{games_per_pair} "
            f"winner={winner_name} "
            f"moves={game['num_moves']} "
            f"time={game['time']:.2f}s"
        )


# ============================================================
# LOADING / SAVING
# ============================================================

def load_existing_results(path):
    if not path.exists():
        return []

    rows = []

    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            row["game_index"] = int(row["game_index"])
            row["swapped"] = row["swapped"] in ("True", "true", "1")
            row["winner_raw"] = int(row["winner_raw"])
            row["num_moves"] = int(row["num_moves"])
            row["time"] = float(row["time"])
            rows.append(row)

    return rows


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def save_csv(path, rows):
    if not rows:
        return

    fieldnames = [
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

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# ============================================================
# SUMMARY
# ============================================================

def summarize(all_results, bot_names):
    summary = {}

    for a in bot_names:
        summary[a] = {}

        for b in bot_names:
            if a == b:
                continue

            games = [
                r for r in all_results
                if {r["bot_a"], r["bot_b"]} == {a, b}
            ]

            if not games:
                continue

            wins_a = sum(1 for r in games if r["winner"] == a)
            wins_b = sum(1 for r in games if r["winner"] == b)
            draws = sum(1 for r in games if r["winner"] == "draw")

            summary[a][b] = {
                "wins": wins_a,
                "losses": wins_b,
                "draws": draws,
                "games": len(games),
                "win_rate": wins_a / len(games),
                "draw_rate": draws / len(games),
                "avg_moves": sum(r["num_moves"] for r in games) / len(games),
                "avg_time": sum(r["time"] for r in games) / len(games),
            }

    return summary


# ============================================================
# PLOTS
# ============================================================

def plot_winrate_heatmap(summary, bot_names, out_path):
    matrix = np.full((len(bot_names), len(bot_names)), np.nan)

    for i, a in enumerate(bot_names):
        for j, b in enumerate(bot_names):
            if a == b:
                continue
            if b in summary[a]:
                matrix[i, j] = summary[a][b]["win_rate"] * 100

    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(matrix, vmin=0, vmax=100)

    ax.set_xticks(range(len(bot_names)))
    ax.set_yticks(range(len(bot_names)))
    ax.set_xticklabels(bot_names, rotation=35, ha="right")
    ax.set_yticklabels(bot_names)

    ax.set_title("Win rate heatmap")
    ax.set_xlabel("Opponent")
    ax.set_ylabel("Bot")

    for i in range(len(bot_names)):
        for j in range(len(bot_names)):
            if i == j:
                ax.text(j, i, "-", ha="center", va="center")
            elif not np.isnan(matrix[i, j]):
                ax.text(j, i, f"{matrix[i, j]:.0f}%", ha="center", va="center")

    fig.colorbar(im, ax=ax, label="Win rate (%)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def plot_total_scores(summary, bot_names, out_path):
    scores = []

    for a in bot_names:
        wins = 0
        draws = 0
        games = 0

        for b in bot_names:
            if a == b:
                continue
            if b not in summary[a]:
                continue

            s = summary[a][b]
            wins += s["wins"]
            draws += s["draws"]
            games += s["games"]

        score = wins + 0.5 * draws
        scores.append((a, score, games))

    labels = [x[0] for x in scores]
    values = [x[1] for x in scores]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(labels, values)

    ax.set_title("Tournament score")
    ax.set_ylabel("Points: win = 1, draw = 0.5")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=35, ha="right")

    for i, v in enumerate(values):
        ax.text(i, v, f"{v:.1f}", ha="center", va="bottom")

    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def plot_avg_moves(summary, bot_names, out_path):
    labels = []
    values = []

    for a in bot_names:
        total_moves = 0
        total_games = 0

        for b in bot_names:
            if a == b:
                continue
            if b not in summary[a]:
                continue

            s = summary[a][b]
            total_moves += s["avg_moves"] * s["games"]
            total_games += s["games"]

        labels.append(a)
        values.append(total_moves / total_games if total_games else 0)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(labels, values)

    ax.set_title("Average game length")
    ax.set_ylabel("Moves")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=35, ha="right")

    for i, v in enumerate(values):
        ax.text(i, v, f"{v:.1f}", ha="center", va="bottom")

    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


# ============================================================
# MAIN
# ============================================================

def main():
    ROOT = Path(__file__).resolve().parent.parent

    old_ckpt = "EvalFunction/net_010000.pt"
    new_ckpt = "EvalFunction/net_015200.pt"

    bots = {
        "Random": RandomBot(),

        "Heuristic": HeuristicBot(max_safety_checks=5),

        "AlphaBeta-new-d3": NeuralAlphaBetaBot(
            checkpoint_path=str(new_ckpt),
            depth=3,
            move_limit=8,
        ),

        "MCTS-old-100": MCTSBot(
            checkpoint_path=str(old_ckpt),
            num_sims=100,
        ),

        "MCTS-new-100": MCTSBot(
            checkpoint_path=str(new_ckpt),
            num_sims=100,
        ),
    }

    bot_names = list(bots.keys())

    out_dir = ROOT / "BotExperiments" / "results" / TOURNAMENT_NAME
    out_dir.mkdir(parents=True, exist_ok=True)

    games_path = out_dir / "games.csv"

    if RESUME:
        all_results = load_existing_results(games_path)
        print(f"Loaded {len(all_results)} existing games from {games_path}")
    else:
        all_results = []

    completed_keys = set()

    for r in all_results:
        if "game_key" in r and r["game_key"]:
            completed_keys.add(r["game_key"])
        else:
            completed_keys.add(game_key(r["bot_a"], r["bot_b"], r["game_index"]))

    config = {
        "tournament_name": TOURNAMENT_NAME,
        "games_per_pair": GAMES_PER_PAIR,
        "max_game_len": MAX_GAME_LEN,
        "bots": bot_names,
        "created_or_resumed_at": datetime.now().isoformat(),
    }

    save_json(out_dir / "config.json", config)

    for i, a in enumerate(bot_names):
        for j, b in enumerate(bot_names):
            if i >= j:
                continue

            print("=" * 80)
            print(f"Running {a} vs {b}")
            print("=" * 80)

            run_pair(
                a,
                bots[a],
                b,
                bots[b],
                games_per_pair=GAMES_PER_PAIR,
                max_game_len=MAX_GAME_LEN,
                all_results=all_results,
                completed_keys=completed_keys,
                out_dir=out_dir,
                bot_names=bot_names,
            )

    summary = summarize(all_results, bot_names)

    save_csv(out_dir / "games.csv", all_results)
    save_json(out_dir / "summary.json", summary)

    plot_winrate_heatmap(summary, bot_names, out_dir / "winrate_heatmap.png")
    plot_total_scores(summary, bot_names, out_dir / "total_scores.png")
    plot_avg_moves(summary, bot_names, out_dir / "avg_moves.png")

    print()
    print("Tournament finished.")
    print("Saved to:", out_dir)


if __name__ == "__main__":
    main()
import os
import json
from datetime import datetime

import sys
from pathlib import Path

import random

REPO_ROOT = Path(__file__).resolve().parent.parent
LOGIX_ROOT = REPO_ROOT / "EvaluationFunction" / "eval_func_v2"

sys.path.insert(0, str(LOGIX_ROOT))


from logix_az.env_logix_helper import LogixShapeEnv
from bots import *


def play_game(bot_p1, bot_p2, max_game_len=100, seed=None, verbose=False):
    env = LogixShapeEnv(n=7, max_game_len=max_game_len, seed=seed)

    moves = []
    done = False
    result = 0

    while not done:
        bot = bot_p1 if env.player == +1 else bot_p2
        player = env.player

        move = bot.choose_move(env)

        if move not in env.legal_moves():
            print(f"Bot chose illegal move: {move}, replacing by random legal move")
            move = random.choice(env.legal_moves())

        _, done, result = env.step(move)

        moves.append({
            "player": player,
            "move": list(move),
        })

        if verbose:
            print(f"turn={env.turn} player={player} move={move}")

    return {
        "winner": int(result),
        "moves": moves,
        "num_moves": len(moves),
    }


def run_match(bot_a, bot_b, games=100, max_game_len=100, swap_sides=True):
    stats = {
        "bot_a_wins": 0,
        "bot_b_wins": 0,
        "draws": 0,
        "games": [],
    }

    for i in range(games):
        if swap_sides and i % 2 == 1:
            p1, p2 = bot_b, bot_a
            swapped = True
        else:
            p1, p2 = bot_a, bot_b
            swapped = False

        game = play_game(p1, p2, max_game_len=max_game_len, seed=None)

        winner = game["winner"]

        if winner == 0:
            stats["draws"] += 1
        else:
            # convert winner to bot_a/b identity
            if not swapped:
                if winner == +1:
                    stats["bot_a_wins"] += 1
                else:
                    stats["bot_b_wins"] += 1
            else:
                if winner == +1:
                    stats["bot_b_wins"] += 1
                else:
                    stats["bot_a_wins"] += 1

        stats["games"].append(game)

        print(
            f"game={i+1}/{games} "
            f"winner={winner} "
            f"moves={game['num_moves']} "
            f"A={stats['bot_a_wins']} "
            f"B={stats['bot_b_wins']} "
            f"D={stats['draws']}"
        )

    return stats


def save_results(stats, name):
    os.makedirs("bot_experiments/results", exist_ok=True)

    path = f"bot_experiments/results/{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    print("saved results:", path)


# def main():
#     ROOT = Path(__file__).resolve().parent.parent

#     checkpoint = (
#         ROOT
#         / "EvaluationFunction"
#         / "eval_func_v2"
#         / "checkpoints"
#         / "net_015200.pt"
#     )

#     bot_a = MCTSBot(str(checkpoint), num_sims=200)
#     bot_b = HeuristicBot()

#     stats = run_match(
#         bot_a,
#         bot_b,
#         games=50,
#         max_game_len=100,
#         swap_sides=True,
#     )

#     save_results(stats, "mcts_vs_heuristic")

# def main():
#     bot_a = RandomBot()
#     bot_b = HeuristicBot()

#     stats = run_match(
#         bot_a,
#         bot_b,
#         games=50,
#         max_game_len=100,
#         swap_sides=True,
#     )

#     save_results(stats, "random_vs_heuristic")

# def main():
#     ROOT = Path(__file__).resolve().parent.parent

#     checkpoint = (
#         ROOT
#         / "EvaluationFunction"
#         / "eval_func_v2"
#         / "checkpoints"
#         / "net_015200.pt"
#     )
#     bot_a = RandomBot()
#     bot_b = NeuralAlphaBetaBot(
#     checkpoint_path=str(checkpoint),
#     depth=3,
#     move_limit=8,
# )

#     stats = run_match(
#         bot_a,
#         bot_b,
#         games=50,
#         max_game_len=100,
#         swap_sides=True,
#     )

#     save_results(stats, "random_vs_alphabeta")

# def main():
#     ROOT = Path(__file__).resolve().parent.parent

#     checkpoint = (
#         ROOT
#         / "EvaluationFunction"
#         / "eval_func_v2"
#         / "checkpoints"
#         / "net_015200.pt"
#     )
#     bot_a = MCTSBot(str(checkpoint), num_sims=500)
#     bot_b = NeuralAlphaBetaBot(
#     checkpoint_path=str(checkpoint),
#     depth=3,
#     move_limit=8,
# )

#     stats = run_match(
#         bot_a,
#         bot_b,
#         games=50,
#         max_game_len=100,
#         swap_sides=True,
#     )

#     save_results(stats, "mcts_vs_alphabeta")

def main():
    ROOT = Path(__file__).resolve().parent.parent

    checkpoint = (
        ROOT
        / "EvaluationFunction"
        / "eval_func_v2"
        / "checkpoints"
        / "net_015200.pt"
    )
    bot_a = MCTSBot(str(checkpoint), num_sims=50)
    bot_b = RandomBot()

    stats = run_match(
        bot_a,
        bot_b,
        games=50,
        max_game_len=100,
        swap_sides=True,
    )

    save_results(stats, "mcts_vs_alphabeta")


if __name__ == "__main__":
    main()
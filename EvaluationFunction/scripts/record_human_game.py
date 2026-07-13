import json
import os
from datetime import datetime

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from logix_az.env_logix_helper import LogixShapeEnv

SAVE_DIR = "recorded_games"


def print_board(env: LogixShapeEnv):
    symbol_map = {
        0: ".",
        1: "R",
        2: "G",
        3: "B",
        4: "Y",
        5: "X",   # Gray
    }

    print()
    print(f"Player to move: {env.player}")
    print(f"Turn: {env.turn}")
    print(f"Banned colors: {sorted(env.banned_colors())}")
    print(f"Inventory: {env.inventory}")
    print("Objectives:")
    for who in (+1, -1):
        print(f"  Player {who}:")
        for i, obj in enumerate(env.objectives[who]):
            print(
                f"    [{i}] shape={obj['shape'].name}, "
                f"assigned_color={obj['assigned_color']}, "
                f"allowed={obj['allowed_win_colors']}"
            )

    print("\nBoard:")
    for r in range(env.n):
        row = []
        for c in range(env.n):
            if env.black[r, c] == 1:
                row.append("K")
            else:
                row.append(symbol_map[int(env.board[r, c])])
        print(" ".join(row))
    print()


def serialize_objectives(objectives):
    out = {}
    for who in (+1, -1):
        out[str(who)] = []
        for obj in objectives[who]:
            out[str(who)].append({
                "shape_name": obj["shape"].name,
                "shape_offsets": [list(x) for x in obj["shape"].offsets],
                "assigned_color": obj["assigned_color"],
                "allowed_win_colors": list(obj["allowed_win_colors"]),
            })
    return out


def serialize_initial_state(env: LogixShapeEnv):
    return {
        "board": env.board.tolist(),
        "black": env.black.tolist(),
        "player": env.player,
        "turn": env.turn,
        "center": list(env.center),
        "last_colors_played": list(env.last_colors_played),
        "inventory": dict(env.inventory),
        "objectives": serialize_objectives(env.objectives),
        "board_size": env.n,
        "max_game_len": env.max_game_len,
    }


def serialize_move(move):
    return list(move)


def save_game_record(record: dict, filename: str | None = None):
    os.makedirs(SAVE_DIR, exist_ok=True)

    if filename is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"logix_game_{ts}.json"

    path = os.path.join(SAVE_DIR, filename)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)

    print(f"\nSaved game to: {path}")


def parse_move(user_input: str):
    parts = user_input.strip().split()
    if not parts:
        return None

    cmd = parts[0].lower()

    try:
        if cmd == "p" and len(parts) == 4:
            color = parts[1]
            x = int(parts[2])
            y = int(parts[3])
            return ("place", x, y, color)

        if cmd == "m" and len(parts) == 5:
            x1 = int(parts[1])
            y1 = int(parts[2])
            x2 = int(parts[3])
            y2 = int(parts[4])
            return ("move", x1, y1, x2, y2)

        if cmd == "r" and len(parts) == 4:
            color = parts[1]
            x = int(parts[2])
            y = int(parts[3])
            return ("replace", x, y, color)
    except ValueError:
        return None

    return None


def normalize_move(move):
    if move is None:
        return None

    typ = move[0]
    if typ in ("place", "replace"):
        typ, x, y, color = move
        color = color.capitalize()
        if color.lower() == "gray":
            color = "Gray"
        return (typ, x, y, color)

    return move


def record_one_game():
    env = LogixShapeEnv(n=7, max_game_len=100, seed=None)
    env.reset()

    game_record = {
        "format_version": 1,
        "created_at": datetime.now().isoformat(),
        "initial_state": serialize_initial_state(env),
        "moves": [],
        "winner": None,
        "finished": False,
    }

    print("Starting a new recorded Logix game.")
    print("Enter moves in these formats:")
    print("  place   -> p COLOR X Y")
    print("  move    -> m X1 Y1 X2 Y2")
    print("  replace -> r COLOR X Y")
    print("Commands:")
    print("  q  -> quit without saving")
    print("  s  -> save unfinished game and quit")
    print("  h  -> show board again")
    print()

    done = False
    result = 0

    while not done:
        print_board(env)

        while True:
            user = input("Move: ").strip()

            if user.lower() == "q":
                print("Quitting without saving.")
                return

            if user.lower() == "s":
                game_record["winner"] = None
                game_record["finished"] = False
                save_game_record(game_record)
                return

            if user.lower() == "h":
                print_board(env)
                continue

            move = normalize_move(parse_move(user))
            if move is None:
                print("Invalid format. Use p COLOR X Y / m X1 Y1 X2 Y2 / r COLOR X Y")
                continue

            legal_moves = env.legal_moves()
            if move not in legal_moves:
                print("Invalid move")
                continue

            break

        perspective_player = env.player
        _, done, result = env.step(move)

        game_record["moves"].append({
            "turn_index": len(game_record["moves"]),
            "player": perspective_player,
            "move": serialize_move(move),
        })

    print_board(env)
    print("Game finished.")
    print("Result:", result)

    game_record["winner"] = int(result)
    game_record["finished"] = True

    save_game_record(game_record)


if __name__ == "__main__":
    record_one_game()
import os
import json
import numpy as np

from logix_az.env_logix import LogixEnv
from logix_az.action_encoding import encode_action, A


def move_to_onehot(move):
    pi = np.zeros((A,), dtype=np.float32)
    a = encode_action(tuple(move))
    pi[a] = 1.0
    return pi


def load_recorded_games(folder="recorded_games"):
    """
    Returns:
        examples = [(state, pi, z), ...]
    """
    env_api = LogixEnv()

    all_examples = []

    files = [
        f for f in os.listdir(folder)
        if f.endswith(".json")
    ]

    print(f"Loading {len(files)} recorded games...")

    for fname in files:
        path = os.path.join(folder, fname)

        with open(path, "r", encoding="utf-8") as f:
            game = json.load(f)

        if not game.get("finished", False):
            continue

        winner = game["winner"]

        # reconstruct helper env
        helper = env_api._unpack_state(
            env_api._pack_state_from_json(game["initial_state"])
        )

        states_and_players = []

        # replay moves
        for item in game["moves"]:
            player = item["player"]
            move = tuple(item["move"])

            state = env_api._pack_state(helper)

            pi = move_to_onehot(move)

            states_and_players.append((state, pi, player))

            helper.step(move)

        # assign z
        for state, pi, player in states_and_players:
            if winner == 0:
                z = 0.0
            elif player == winner:
                z = 1.0
            else:
                z = -1.0

            all_examples.append((state, pi, z))

    print(f"Loaded {len(all_examples)} human examples.")
    return all_examples
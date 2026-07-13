from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# from env_logix_helper import LogixShapeEnv
# from action_encoding import encode_action, decode_action

# env = LogixShapeEnv()
# env.reset()

# moves = env.legal_moves()

# for mv in moves:
#     a = encode_action(mv)
#     mv2 = decode_action(a)
#     if mv != mv2:
#         print("Mismatch:", mv, a, mv2)

# print("Done")

####################

# import torch
# print(torch.__version__)
# print(torch.cuda.is_available())
# print(torch.cuda.device_count())
# print(torch.version.cuda)

####################

# from env_logix_helper import LogixShapeEnv, COLOR_CODE


# def print_board(env):
#     for r in range(env.n):
#         row = []
#         for c in range(env.n):
#             if env.black[r, c] == 1:
#                 row.append("K")
#             else:
#                 v = env.board[r, c]
#                 if v == 0:
#                     row.append(".")
#                 elif v == COLOR_CODE["R"]:
#                     row.append("R")
#                 elif v == COLOR_CODE["G"]:
#                     row.append("G")
#                 elif v == COLOR_CODE["B"]:
#                     row.append("B")
#                 elif v == COLOR_CODE["Y"]:
#                     row.append("Y")
#                 elif v == COLOR_CODE["Gray"]:
#                     row.append("X")
#                 else:
#                     row.append("?")
#         print(" ".join(row))
#     print()


# def test_line_win():
#     env = LogixShapeEnv(n=7)
#     env.reset()

#     r, c = env.center  # usually (3,3)

#     # seven shape
#     # (r,c-2), (r,c-1), (r,c), (r,c+1), (r,c+2)
#     positions = [
#         (r, c - 2),
#         (r, c - 1),
#         (r, c),
#         (r - 1, c - 1),
#         (r + 1, c - 2),
#     ]

#     for rr, cc in positions:
#         if (rr, cc) != (r, c):  # skip black cell
#             env.board[rr, cc] = COLOR_CODE["R"]

#     print("Board:")
#     print_board(env)

#     print("Objectives:")
#     print(env.objectives)
#     print()

#     for player in (+1, -1):
#         result = env._check_win_for_player(player)
#         print(f"Player {player} win: {result}")


# if __name__ == "__main__":
#     test_line_win()

#######################

# from logix_az.env_logix_helper import LogixShapeEnv, COLOR_CODE
# from logix_az.env_logix import LogixEnv
# from logix_az.action_encoding import encode_action


# def print_board_from_state(state):
#     for r in range(state.board.shape[0]):
#         row = []
#         for c in range(state.board.shape[1]):
#             v = state.board[r, c]
#             if v == 0:
#                 row.append(".")
#             elif v == 9:
#                 row.append("K")
#             elif v == COLOR_CODE["R"]:
#                 row.append("R")
#             elif v == COLOR_CODE["G"]:
#                 row.append("G")
#             elif v == COLOR_CODE["B"]:
#                 row.append("B")
#             elif v == COLOR_CODE["Y"]:
#                 row.append("Y")
#             elif v == COLOR_CODE["Gray"]:
#                 row.append("X")
#             else:
#                 row.append("?")
#         print(" ".join(row))
#     print()


# def test_wrapper_step_win():
#     helper = LogixShapeEnv(n=7, max_game_len=100)
#     helper.reset()

#     helper.player = +1
#     helper.turn = 0
#     helper.last_colors_played = set()
#     helper.inventory = {"R": 10, "G": 10, "B": 10, "Y": 10, "Gray": 10}

#     r, c = helper.center

#     # one move away from Seven-Shape@0 win
#     already_filled = [
#         (r + 1, c),
#         (r + 2, c),
#         (r + 2, c - 1),
#     ]

#     for rr, cc in already_filled:
#         helper.board[rr, cc] = COLOR_CODE["R"]

#     env = LogixEnv(seed=0, n=7, max_game_len=100)
#     state = env._pack_state(helper)

#     print("Before winning move:")
#     print_board_from_state(state)
#     print("is_terminal before:", env.is_terminal(state))

#     move = ("place", r + 1, c + 1, "R")
#     action = encode_action(move)

#     next_state = env.step(state, action)

#     print("\nAfter winning move:")
#     print_board_from_state(next_state)
#     print("is_terminal after:", env.is_terminal(next_state))
#     print("outcome after:", env.outcome(next_state))


# if __name__ == "__main__":
#     test_wrapper_step_win()



#########################
# cheking correctness of check win

from logix_az.env_logix_helper import LogixShapeEnv, COLOR_CODE, WinShape


def print_board(env):
    decode = {
        0: ".",
        1: "R",
        2: "G",
        3: "B",
        4: "Y",
        5: "X",
    }
    for r in range(env.n):
        row = []
        for c in range(env.n):
            if env.black[r, c] == 1:
                row.append("K")
            else:
                row.append(decode[int(env.board[r, c])])
        print(" ".join(row))
    print()


def force_cshape_objective(env):
    env.objectives = {
        +1: [
            {
                "shape": WinShape("C-Shape", ((0, 0), (1, 0), (2, 0), (0, 1), (2, 1))),
                "assigned_color": "Y",   # red allowed
                "allowed_win_colors": ("R", "G", "B"),
            },
            {
                "shape": WinShape("Line", ((0, 0), (1, 0), (2, 0), (3, 0), (4, 0))),
                "assigned_color": "G",
                "allowed_win_colors": ("R", "B", "Y"),
            },
        ],
        -1: [
            {
                "shape": WinShape("Plus", ((0, 0), (1, 0), (0, 1), (-1, 0), (0, -1))),
                "assigned_color": "R",
                "allowed_win_colors": ("G", "B", "Y"),
            },
            {
                "shape": WinShape("Seven-Shape", ((0, 0), (1, 0), (2, 0), (2, -1), (1, 1))),
                "assigned_color": "B",
                "allowed_win_colors": ("R", "G", "Y"),
            },
        ],
    }


def fresh_env_with_black_at(br, bc):
    env = LogixShapeEnv(n=7, max_game_len=100)
    env.reset()

    env.board[:, :] = 0
    env.black[:, :] = 0
    env.black[br, bc] = 1
    env.center = (br, bc)

    env.player = +1
    env.turn = 0
    env.last_colors_played = set()
    env.inventory = {"R": 20, "G": 20, "B": 20, "Y": 20, "Gray": 20}

    force_cshape_objective(env)
    return env


def place_red_cells(env, cells):
    for r, c in cells:
        if env.black[r, c] == 1:
            continue
        env.board[r, c] = COLOR_CODE["R"]


def run_direct_test(name, black_pos, red_cells, expected=True):
    print(f"=== DIRECT TEST: {name} ===")
    env = fresh_env_with_black_at(*black_pos)
    place_red_cells(env, red_cells)
    print_board(env)

    p1 = env._check_win_for_player(+1)
    p2 = env._check_win_for_player(-1)

    print("Player +1 win:", p1)
    print("Player -1 win:", p2)

    assert p1 is expected, f"Expected Player +1 win = {expected}, got {p1}"
    assert p2 is False, f"Expected Player -1 win = False, got {p2}"
    print("PASS\n")


def run_step_test(name, black_pos, red_cells_before, winning_move):
    print(f"=== STEP TEST: {name} ===")
    env = fresh_env_with_black_at(*black_pos)
    place_red_cells(env, red_cells_before)

    print("Before move:")
    print_board(env)
    print("Check before move:", env._check_win_for_player(env.player))
    print("Applying:", winning_move)

    _, done, result = env.step(winning_move)

    print("\nAfter move:")
    print_board(env)
    print("done:", done)
    print("result:", result)
    print("Check after move:", env._check_win_for_player(env.player))

    assert done is True, "Expected game to end after winning move."
    assert result == 1, f"Expected result = 1, got {result}"
    print("PASS\n")


def main():
    # -------------------------------------------------------
    # Variant 1: U-shape around black
    #
    # K on top middle of a U:
    # . K .
    # R . R
    # R R R   (with black replacing the top-middle cell conceptually)
    #
    # Actual occupied cells:
    # black center, left, right, down-left, down-right
    # -------------------------------------------------------
    run_direct_test(
        name="U-shape, black at center-ish",
        black_pos=(3, 3),
        red_cells=[
            (3, 2),
            (3, 4),
            (4, 2),
            (4, 4),
        ],
        expected=True,
    )

    # -------------------------------------------------------
    # Variant 2: rotated / reversed C-like orientation
    # Black moved to different board spot
    # -------------------------------------------------------
    run_direct_test(
        name="Reverse-C-like orientation, black near upper-left",
        black_pos=(3, 2),
        red_cells=[
            (1, 2),
            (1, 3),
            (2, 3),
            (3, 3),
        ],
        expected=True,
    )

    # -------------------------------------------------------
    # Variant 3: another rotation with black lower on board
    # -------------------------------------------------------
    run_direct_test(
        name="Another rotated orientation, black lower-middle",
        black_pos=(4, 4),
        red_cells=[
            (3, 2),
            (3, 3),
            (3, 4),
            (4, 2),
        ],
        expected=True,
    )

    # -------------------------------------------------------
    # Negative test: mirrored shape should NOT count
    # (assuming your rule is rotation only, no mirror)
    # -------------------------------------------------------
    run_direct_test(
        name="Mirrored variant",
        black_pos=(3, 3),
        red_cells=[
            (2, 2),
            (2, 4),
            (3, 2),
            (3, 4),
        ],
        expected=True,
    )

    # -------------------------------------------------------
    # One-move-to-win through step()
    # -------------------------------------------------------
    run_step_test(
        name="One move away from U-shape win",
        black_pos=(3, 3),
        red_cells_before=[
            (3, 2),
            (4, 2),
            (4, 4),
        ],
        winning_move=("place", 3, 4, "R"),
    )

    print("All tests passed.")


if __name__ == "__main__":
    main()

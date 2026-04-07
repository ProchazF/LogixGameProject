from env_logix_helper import LogixShapeEnv


def render_board(env):
    """
    Pretty print board.
    . = empty
    K = black
    R/G/B/Y = colors
    X = gray
    """
    symbol_map = {
        0: ".",
        1: "R",
        2: "G",
        3: "B",
        4: "Y",
        5: "X",
    }

    print(f"player to move: {env.player}")
    print(f"turn: {env.turn}")
    print(f"banned colors: {sorted(env.banned_colors())}")
    print(f"shared inventory: {env.inventory}")
    print()

    for r in range(env.n):
        row = []
        for c in range(env.n):
            if env.black[r, c] == 1:
                row.append("K")
            else:
                row.append(symbol_map[int(env.board[r, c])])
        print(" ".join(row))
    print()


def print_legal_moves(env, limit=None, title="LEGAL MOVES"):
    moves = env.legal_moves()
    print(f"=== {title} ===")
    print(f"number of legal moves: {len(moves)}")

    if limit is None:
        limit = len(moves)

    for i, mv in enumerate(moves[:limit]):
        print(f"[{i}] {mv}")

    if len(moves) > limit:
        print(f"... and {len(moves) - limit} more")
    print()

    return moves


def apply_and_show(env, move, show_next_moves=True, next_limit=100):
    print("APPLYING MOVE:", move)
    obs, done, result = env.step(move)

    render_board(env)
    print("done:", done)
    print("result:", result)
    print()

    if show_next_moves and not done:
        print_legal_moves(env, limit=next_limit, title="LEGAL MOVES AFTER APPLIED MOVE")

    return obs, done, result


def inspect_first_moves(env, count=5, next_limit=50):
    moves = env.legal_moves()

    print(f"=== TRY FIRST {min(count, len(moves))} MOVES ON FRESH COPIES ===")
    for i, mv in enumerate(moves[:count]):
        print("=" * 60)
        print(f"TEST MOVE [{i}] {mv}")

        test_env, done, result = env.simulate_move(mv)

        render_board(test_env)
        print("done:", done)
        print("result:", result)
        print()

        print_legal_moves(
            test_env,
            limit=next_limit,
            title=f"LEGAL MOVES AFTER TEST MOVE [{i}]"
        )


def inventory_sanity_check(env, limit=20):
    """
    Checks shared inventory behavior:
      - place: placed color should go down by 1
      - move: inventory should not change
      - replace: inserted color should go down by 1, removed color should go up by 1
    """
    print("=== INVENTORY SANITY CHECK ===")
    moves = env.legal_moves()

    for mv in moves[:limit]:
        before = dict(env.inventory)
        test_env, done, result = env.simulate_move(mv)
        after = dict(test_env.inventory)

        print(f"move:   {mv}")
        print(f"before: {before}")
        print(f"after:  {after}")
        print()

    print("Check whether the inventory changes match the move type.\n")


def black_move_sanity_check(env):
    """
    Shows whether black can move and whether black can be replaced.
    """
    print("=== BLACK MOVE CHECK ===")
    moves = env.legal_moves()

    black_moves = [m for m in moves if m[0] == "move" and env.black[m[1], m[2]] == 1]
    black_replaces = [m for m in moves if m[0] == "replace" and env.black[m[1], m[2]] == 1]
    illegal_place_on_black = [m for m in moves if m[0] == "place" and env.black[m[1], m[2]] == 1]

    print("moves that move black:", len(black_moves))
    for m in black_moves[:20]:
        print("  ", m)

    print("moves that replace black:", len(black_replaces))
    for m in black_replaces[:20]:
        print("  ", m)

    print("moves that place on black:", len(illegal_place_on_black))
    for m in illegal_place_on_black[:20]:
        print("  ", m)

    print()


def banned_color_sanity_check(env):
    """
    After each tested move, print the resulting banned color set.
    """
    print("=== BANNED COLOR SANITY CHECK ===")
    moves = env.legal_moves()

    for mv in moves[:15]:
        test_env, done, result = env.simulate_move(mv)
        print(f"move: {mv}")
        print(f"resulting banned colors: {sorted(test_env.banned_colors())}")
        print()


def main():
    env = LogixShapeEnv(n=7, max_game_len=90)
    env.reset()

    print("=== INITIAL STATE ===")
    render_board(env)
    moves = print_legal_moves(env, limit=100)

    black_move_sanity_check(env)
    inventory_sanity_check(env, limit=20)
    banned_color_sanity_check(env)
    inspect_first_moves(env, count=5, next_limit=100)

    while True:
        user = input("Enter move index to apply, 'r' to refresh legal moves, or 'q' to quit: ").strip()

        if user.lower() == "q":
            break

        if user.lower() == "r":
            render_board(env)
            moves = print_legal_moves(env, limit=100)
            continue

        try:
            idx = int(user)
        except ValueError:
            print("Please enter a valid integer, 'r', or 'q'.\n")
            continue

        if idx < 0 or idx >= len(moves):
            print("Index out of range.\n")
            continue

        move = moves[idx]
        apply_and_show(env, move, show_next_moves=True, next_limit=100)
        moves = print_legal_moves(env, limit=100, title="UPDATED LEGAL MOVES")


if __name__ == "__main__":
    main()
import numpy as np

N = 7
COLORS = ("R", "G", "B", "Y", "Gray")
COLOR_TO_IDX = {c: i for i, c in enumerate(COLORS)}

# -------------------------------------------------------------------
# Action layout
#
# 1) PLACE   : ("place", r, c, color)
# 2) MOVE    : ("move", r1, c1, r2, c2)
# 3) REPLACE : ("replace", r, c, color)
# -------------------------------------------------------------------

PLACE_OFFSET = 0
PLACE_SIZE = N * N * len(COLORS)

MOVE_OFFSET = PLACE_OFFSET + PLACE_SIZE
MOVE_SIZE = N * N * N * N   # from cell -> to cell

REPLACE_OFFSET = MOVE_OFFSET + MOVE_SIZE
REPLACE_SIZE = N * N * len(COLORS)

A = PLACE_SIZE + MOVE_SIZE + REPLACE_SIZE

# returns unique int for each cell
def _cell_to_idx(r: int, c: int) -> int:
    return r * N + c

# returns coordinates for each cell from int
def _idx_to_cell(idx: int) -> tuple[int, int]:
    return idx // N, idx % N


def decode_action(a: int):
    """
    Convert integer action id -> helper-compatible tuple:
      ("place", r, c, color)
      ("move", r1, c1, r2, c2)
      ("replace", r, c, color)
    """
    if a < 0 or a >= A:
        raise ValueError(f"action out of range: {a}")

    # PLACE
    if a < PLACE_OFFSET + PLACE_SIZE:
        t = a - PLACE_OFFSET
        cell = t // len(COLORS)
        color_idx = t % len(COLORS)
        r, c = _idx_to_cell(cell)
        color = COLORS[color_idx]
        return ("place", r, c, color)

    # MOVE
    if a < MOVE_OFFSET + MOVE_SIZE:
        t = a - MOVE_OFFSET
        from_idx = t // (N * N)
        to_idx = t % (N * N)
        r1, c1 = _idx_to_cell(from_idx)
        r2, c2 = _idx_to_cell(to_idx)
        return ("move", r1, c1, r2, c2)

    # REPLACE
    t = a - REPLACE_OFFSET
    cell = t // len(COLORS)
    color_idx = t % len(COLORS)
    r, c = _idx_to_cell(cell)
    color = COLORS[color_idx]
    return ("replace", r, c, color)


def encode_action(move) -> int:
    """
    Convert helper-compatible tuple -> integer action id.
    """
    type = move[0]

    if type == "place":
        _, r, c, color = move
        cell = _cell_to_idx(r, c)
        return PLACE_OFFSET + cell * len(COLORS) + COLOR_TO_IDX[color]

    if type == "move":
        _, r1, c1, r2, c2 = move
        from_idx = _cell_to_idx(r1, c1)
        to_idx = _cell_to_idx(r2, c2)
        return MOVE_OFFSET + from_idx * (N * N) + to_idx

    if type == "replace":
        _, r, c, color = move
        cell = _cell_to_idx(r, c)
        return REPLACE_OFFSET + cell * len(COLORS) + COLOR_TO_IDX[color]

    raise ValueError(f"unknown move type: {type}")
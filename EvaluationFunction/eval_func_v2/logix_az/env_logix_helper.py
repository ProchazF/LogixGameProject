import os
import random
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional, Iterable
from collections import deque

import numpy as np

# ============================================================
# Win shapes + assignment (rotations only; no mirrors)
# ============================================================

Vec = Tuple[int, int]

@dataclass(frozen=True)
class WinShape:
    name: str
    offsets: Tuple[Vec, ...]  # relative to anchor (0,0) which MUST be part of the shape (the black cell)

def rot90(v: Vec) -> Vec:
    x, y = v
    return (-y, x)

def rotate(shape: WinShape, k: int) -> WinShape:
    offs = shape.offsets
    for _ in range(k % 4):
        offs = tuple(rot90(o) for o in offs)
    return WinShape(f"{shape.name}@{(k%4)*90}", offs)

COLORS = ("R", "G", "B", "Y")  # base colors
COLOR_TO_IDX = {c:i for i,c in enumerate(COLORS)}  # R=0,G=1,B=2,Y=3

ALL_SHAPES: Tuple[WinShape, ...] = (
    WinShape("Line",                 ((0,0),(1,0),(2,0),(3,0),(4,0))),
    WinShape("Plus",                 ((0,0),(1,0),(0,1),(-1,0),(0,-1))),
    WinShape("T-Shape",              ((0,0),(1,0),(2,0),(2,-1),(2,1))),
    WinShape("Long L-Shape Mirrored",((0,0),(1,0),(2,0),(3,0),(3,1))),
    WinShape("Long L-Shape",         ((0,0),(1,0),(2,0),(3,0),(3,-1))),
    WinShape("Short L-Shape",        ((0,0),(1,0),(2,0),(2,1),(2,2))),
    WinShape("Seven-Shape",          ((0,0),(1,0),(2,0),(2,-1),(1,1))),
    WinShape("Mirrored Seven-Shape", ((0,0),(1,0),(2,0),(1,-1),(2,1))),
    WinShape("C-Shape",              ((0,0),(1,0),(2,0),(0,1),(2,1))),
    WinShape("Stair-Shape",          ((0,0),(1,0),(1,1),(2,1),(2,2))),
    WinShape("Z-Shape",              ((0,0),(1,0),(2,0),(2,-1),(0,1))),
    WinShape("Reverse Z-Shape",      ((0,0),(1,0),(2,0),(2,1),(0,-1))),
    WinShape("One-Shape",            ((0,0),(1,0),(2,0),(2,-1),(3,0))),
    WinShape("Reverse One-Shape",    ((0,0),(1,0),(2,0),(2,1),(3,0))),
    WinShape("d-shape",              ((0,0),(1,0),(2,0),(0,1),(1,1))),
    WinShape("b-shape",              ((0,0),(1,0),(0,1),(1,1),(2,1))),
    WinShape("Snake",                ((0,0),(1,0),(2,0),(2,-1),(3,-1))),
    WinShape("Reverse Snake",        ((0,0),(1,0),(2,0),(2,1),(3,1))),
)

def assign_player_objectives(rng: random.Random = random) -> Dict[int, List[Dict[str, object]]]:
    """
    Give each player two objectives. Each objective has:
      - shape (with a random rotation)
      - assigned_color
      - allowed_win_colors (all base colors except the assigned one)
    """
    def sample_two():
        # pick two *different* base shapes (rotations applied after)
        s1, s2 = rng.sample(list(ALL_SHAPES), 2)
        o1 = rotate(s1, rng.randrange(4))
        o2 = rotate(s2, rng.randrange(4))
        a1 = rng.choice(COLORS)
        a2 = rng.choice(COLORS)
        return [
            {"shape": o1, "assigned_color": a1, "allowed_win_colors": tuple(c for c in COLORS if c != a1)},
            {"shape": o2, "assigned_color": a2, "allowed_win_colors": tuple(c for c in COLORS if c != a2)},
        ]
    return {+1: sample_two(), -1: sample_two()}

def iter_rotations(shape: WinShape) -> Iterable[WinShape]:
    for k in range(4):
        yield rotate(shape, k)

def shape_world_positions(anchor: Tuple[int,int], shape: WinShape) -> List[Tuple[int,int]]:
    ar, ac = anchor
    return [(ar + dr, ac + dc) for (dr, dc) in shape.offsets]

# ============================================================
# Config
# ============================================================

@dataclass
class Config:
    board_size: int = 7

    # Input planes (C,H,W):
    # 5 color planes: R,G,B,Y,Gray
    # 1 black plane
    # 1 legal mask plane (placement/move/replace destinations share this proximity)
    # 4 banned-color one-hot (R,G,B,Y), tiled
    # 1 parity plane (+1/-1)
    # 1 bias plane (ones)
    in_planes: int = 13

    batch_size: int = 1024
    replay_capacity: int = 200_000
    min_replay_to_train: int = 10_000
    lr: float = 1e-3
    save_every_secs: int = 3600
    print_every_episodes: int = 100
    max_game_len: int = 90
    epsilon_start: float = 0.60
    epsilon_end: float = 0.08
    epsilon_anneal_episodes: int = 25_000
    value_clip: float = 1.0
    ckpt_dir: str = "checkpoints"
    onnx_name: str = "value_net.onnx"
    model_name: str = "value_net.pt"
    seed: int = 42

CFG = Config()
random.seed(CFG.seed)
np.random.seed(CFG.seed)
os.makedirs(CFG.ckpt_dir, exist_ok=True)

# ============================================================
# Environment with place / move / replace, bans, inventory, win check
# ============================================================

# Board encoding:
# 0 empty
# 1 R, 2 G, 3 B, 4 Y, 5 Gray, 9 Black
COLOR_CODE = {"R":1, "G":2, "B":3, "Y":4, "Gray":5, "Black":9}
IDX_TO_COLOR = {1:"R", 2:"G", 3:"B", 4:"Y", 5:"Gray", 9:"Black"}

InventoryDict = Dict[str, int]

class LogixShapeEnv:
    def __init__(self, n=7, max_game_len=100):
        self.n = n
        self.max_game_len = max_game_len
        self.reset()

    def reset(self):
        self.board = np.zeros((self.n, self.n), dtype=np.int8)
        self.player = +1  # +1 or -1
        self.turn = 0

        # Place black at center
        self.black = np.zeros_like(self.board, dtype=np.int8)
        c = self.n // 2
        self.black[c, c] = 1
        self.center = (c, c)

        # Last color played
        self.last_colors_played = set()

        # inventory
        self.inventory = {"R": 6, "G": 6, "B": 6, "Y": 6, "Gray": 2}

        # Per-episode objectives
        self.objectives = assign_player_objectives()

        return self._obs()

    # ------------- Helper masks & utils -------------

    def inside(self, r, c):
        return 0 <= r < self.n and 0 <= c < self.n

    def _occupied_mask(self):
        return (self.board != 0) | (self.black == 1)

    def _adjacent_mask(self):
        """Cells orthogonally adjacent to any occupied (including black)."""
        mask = np.zeros_like(self.board, dtype=np.int8)
        occ = self._occupied_mask()
        for r in range(self.n):
            for c in range(self.n):
                if occ[r, c]:
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        rr, cc = r+dr, c+dc
                        if self.inside(rr,cc) and self.board[rr, cc] == 0:
                            mask[rr, cc] = 1
        if not mask.any():
            # allow around black (safety)
            cr, cc = self.center
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                rr, cc2 = cr+dr, cc+dc
                if self.inside(rr,cc2) and self.board[rr, cc2] == 0:
                    mask[rr, cc2] = 1
        return mask

    def banned_colors(self) -> set[str]:
        """
        Global ban set produced by the immediately previous move.
        """
        return set(self.last_colors_played)

    def _is_blocked_piece(self, r: int, c: int) -> bool:
        """Blocked if all 4 neighbors are occupied (board or black)."""
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            rr, cc = r+dr, c+dc
            if self.inside(rr, cc) and self.board[rr, cc] == 0 and self.black[rr, cc] == 0:
                return False
        return True
    
    def _can_reach(self, r1: int, c1: int, r2: int, c2: int) -> bool:
        """
        Returns True if a marble picked up from (r1, c1) can reach (r2, c2)
        by moving through empty cells using only 4-neighborhood moves.

        Important:
        - destination must also be empty in the current position
        - black and normal marbles both block movement
        """
        if not self.inside(r1, c1) or not self.inside(r2, c2):
            return False

        if (r1, c1) == (r2, c2):
            return False

        # destination must be empty right now
        if self.board[r2, c2] != 0 or self.black[r2, c2] == 1:
            return False

        visited = np.zeros((self.n, self.n), dtype=bool)
        q = deque()

        # start from the source square, treated as empty after lifting the marble
        q.append((r1, c1))
        visited[r1, c1] = True

        while q:
            r, c = q.popleft()

            if (r, c) == (r2, c2):
                return True

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                rr, cc = r + dr, c + dc

                if not self.inside(rr, cc):
                    continue
                if visited[rr, cc]:
                    continue

                # the source square is treated as empty
                if (rr, cc) == (r1, c1):
                    visited[rr, cc] = True
                    q.append((rr, cc))
                    continue

                # otherwise only empty cells are traversable
                if self.board[rr, cc] == 0 and self.black[rr, cc] == 0:
                    visited[rr, cc] = True
                    q.append((rr, cc))

        return False
    
    # return adjacent marbles without source
    def _adjacent_mask_without_source(self, sr: int, sc: int) -> np.ndarray:
        """
        Cells orthogonally adjacent to any occupied cell, but treat (sr, sc)
        as empty because that marble is being lifted for a move.
        """
        mask = np.zeros_like(self.board, dtype=np.int8)

        for r in range(self.n):
            for c in range(self.n):
                # treat source as empty
                if (r, c) == (sr, sc):
                    occupied = False
                else:
                    occupied = (self.board[r, c] != 0) or (self.black[r, c] == 1)

                if not occupied:
                    continue

                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    rr, cc = r + dr, c + dc
                    if not self.inside(rr, cc):
                        continue

                    # destination cell itself must currently be empty,
                    # except source which we also treat as empty
                    if (rr, cc) == (sr, sc):
                        mask[rr, cc] = 1
                    elif self.board[rr, cc] == 0 and self.black[rr, cc] == 0:
                        mask[rr, cc] = 1

        return mask

    # ------------- Actions listing -------------

    def legal_moves(self) -> List[Tuple]:
        """
        Returns a list of *action tuples*:
          - ('place', r, c, color)
          - ('move', r1, c1, r2, c2)          # source must not be fully blocked
          - ('replace', r, c, color)          # replace board cell with a color from inventory
        All obey the banned-color rule (including Gray).
        Placement/move destinations must be adjacent to any occupied (proximity rule).
        """
        acts = []
        banned = self.banned_colors()
        adj = self._adjacent_mask()

        inv = self.inventory

        # --- PLACE: from inventory to empty adj cell ---
        for r in range(self.n):
            for c in range(self.n):
                if adj[r, c] != 1: continue
                if self.board[r, c] != 0 or self.black[r, c] == 1: continue
                for col in ("R","G","B","Y","Gray"):
                    if col in banned: continue
                    if inv[col] <= 0: continue
                    acts.append(("place", r, c, col))

        # --- MOVE: move an existing marble to empty adj cell ---
        for r1 in range(self.n):
            for c1 in range(self.n):
                v = self.board[r1, c1]
                has_normal_piece = self.board[r1, c1] != 0
                has_black_piece = self.black[r1, c1] == 1

                move_adj = self._adjacent_mask_without_source(r1, c1)

                if not has_normal_piece and not has_black_piece:
                    continue
                # require not fully blocked (simplified rule)
                if self._is_blocked_piece(r1, c1):
                    continue
                if has_black_piece:
                    moved_color = "Black"
                else:
                    v = self.board[r1, c1]
                    moved_color = IDX_TO_COLOR[v]
                if moved_color in banned:
                    continue
                for r2 in range(self.n):
                    for c2 in range(self.n):
                        if r1 == r2 and c1 == c2: continue # cant move in place
                        if self.board[r2, c2] != 0: continue
                        if self.black[r2, c2] == 1:continue
                        if move_adj[r2, c2] != 1: continue
                        if not self._can_reach(r1, c1, r2, c2): continue
                        acts.append(("move", r1, c1, r2, c2))

        # --- REPLACE: swap board cell with inventory color (no dest proximity check needed) ---
        for r in range(self.n):
            for c in range(self.n):
                v = self.board[r, c]
                if v == 0: continue
                if self.black[r, c] == 1: continue  # cannot replace black
                cur_color = IDX_TO_COLOR.get(v, "Gray") if v in (1,2,3,4) else "Gray"
                if cur_color in banned: continue # cannot replace banned color
                for col in ("R","G","B","Y","Gray"):
                    if col in banned: continue
                    if inv[col] <= 0: continue
                    if col == cur_color: continue  # replacing by same color is pointless
                    acts.append(("replace", r, c, col))

        return acts

    # ------------- Win check -------------

    def _check_no_adjacent_same_color(self, cells: List[Tuple[int,int]], base_code: int) -> bool:
        """Ensure no 4-neighbor cell *outside the shape* contains the same base color."""
        S = set(cells)
        for (r, c) in cells:
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                rr, cc = r+dr, c+dc
                if not self.inside(rr, cc): continue
                if (rr, cc) in S: continue
                if self.board[rr, cc] == base_code:
                    return False
        return True

    def _check_win_for_player(self, who: int) -> bool:
        """
        Win if ANY of the player's two objectives is satisfied:
        - shape completed around the center black with a single base color (R/G/B/Y)
        - Gray and Black are wildcards
        - base color != that objective's assigned color
        - and NO adjacent same-colored marbles touch the finished shape (4-neighborhood).
        """
        objectives = self.objectives[who]

        for obj in objectives:
            assigned = obj["assigned_color"]
            shape = obj["shape"]

            for shp in iter_rotations(shape):
                cells = shape_world_positions(self.center, shp)
                if any(not self.inside(r,c) for (r,c) in cells):
                    continue

                vals = [(9 if self.black[r,c]==1 else self.board[r,c]) for (r,c) in cells]
                if any(v == 0 for v in vals):
                    continue

                present_base = [v for v in vals if v in (1,2,3,4)]
                if len(present_base) == 0:
                    continue
                base_code = present_base[0]

                if not all(v in (base_code, 5, 9) for v in vals):
                    continue

                base_color = IDX_TO_COLOR[base_code]
                if base_color == assigned:
                    continue

                if not self._check_no_adjacent_same_color(cells, base_code):
                    continue

                # this objective is satisfied
                return True

        return False


    # ------------- Apply action -------------

    def step(self, action: Tuple):
        """
        Apply action. Returns (obs, done, result_abs) where result_abs is +1/-1/0.
        Actions:
          ('place', r, c, color)
          ('move', r1, c1, r2, c2)
          ('replace', r, c, color)
        """
        typ = action[0]
        banned = self.banned_colors()
        inv = self.inventory

        if typ == "place":
            _, r, c, col = action
            assert self.board[r, c] == 0, "Illegal: occupied"
            assert self._adjacent_mask()[r, c] == 1, "Illegal: not adjacent for placement"
            assert col not in banned, f"Illegal: color {col} is banned"
            assert inv[col] > 0, f"No inventory for {col}"
            self.board[r, c] = COLOR_CODE[col]
            inv[col] -= 1
            self.last_colors_played = {col}

        elif typ == "move":
            _, r1, c1, r2, c2 = action

            has_normal_piece = self.board[r1, c1] != 0
            has_black_piece = self.black[r1, c1] == 1

            assert has_normal_piece or has_black_piece, "Illegal: no piece at source"
            assert not self._is_blocked_piece(r1, c1), "Illegal: source piece is fully blocked"
            assert self.board[r2, c2] == 0, "Illegal: destination occupied"
            assert self.black[r2, c2] == 0, "Illegal: destination has black"
            assert self._adjacent_mask_without_source(r1, c1)[r2, c2] == 1, "Illegal: destination not adjacent"
            assert self._can_reach(r1, c1, r2, c2), "Illegal: destination not reachable"

            if has_black_piece:
                assert "Black" not in banned, "Illegal: black is banned"
                self.black[r1, c1] = 0
                self.black[r2, c2] = 1
                self.center = (r2, c2)
                self.last_colors_played = {"Black"}
            else:
                v = self.board[r1, c1]
                moved_color = IDX_TO_COLOR[v]
                assert moved_color not in banned, f"Illegal: color {moved_color} is banned"

                self.board[r1, c1] = 0
                self.board[r2, c2] = v
                self.last_colors_played = {moved_color}

        elif typ == "replace":
            _, r, c, col = action
            v = self.board[r, c]
            assert v != 0 and self.black[r, c] == 0, "Illegal: cannot replace empty or black"
            cur_color = IDX_TO_COLOR.get(v, "Gray") if v in (1,2,3,4) else "Gray"
            assert col != cur_color, "Illegal: replacing by same color is pointless"
            assert col not in banned, f"Illegal: color {col} is banned"
            assert inv[col] > 0, f"No inventory for {col}"
            # do swap: take board piece into inventory, place chosen color from inventory
            # removal:
            if v in (1,2,3,4):
                inv[IDX_TO_COLOR[v]] += 1
            else:
                inv["Gray"] += 1
            # placement:
            self.board[r, c] = COLOR_CODE[col]
            inv[col] -= 1
            self.last_colors_played = {cur_color, col}

        else:
            raise ValueError("Unknown action type")

        self.turn += 1

        # terminal check
        if self._check_win_for_player(self.player):
            done = True
            result_abs = +1 if self.player == +1 else -1
        elif self.turn >= self.max_game_len:
            done = True
            result_abs = 0
        else:
            done = False
            result_abs = 0

        if not done:
            self.player *= -1

        return self._obs(), done, result_abs

    # ------------- Simulation clone -------------

    def simulate_move(self, action):
        new_env = LogixShapeEnv(self.n, self.max_game_len)
        new_env.board = self.board.copy()
        new_env.player = self.player
        new_env.turn = self.turn
        new_env.black = self.black.copy()
        new_env.center = tuple(self.center)
        new_env.last_colors_played = set(self.last_colors_played)
        # deep copy inventories
        new_env.inventory = dict(self.inventory)
        # deep copy objectives
        new_env.objectives = {
            +1: [dict(o) for o in self.objectives[+1]],
            -1: [dict(o) for o in self.objectives[-1]],
        }
        _, done, res = new_env.step(action)
        return new_env, done, res

    # ------------- Perspective & observation -------------

    def result_from_perspective(self, final_result: int, perspective_player: int) -> int:
        return final_result if perspective_player == +1 else -final_result

    def _obs(self):
        # 5 color planes: R,G,B,Y,Gray
        planes = []
        for k in (1,2,3,4,5):
            planes.append( (self.board==k).astype(np.float32) )
        # black plane
        planes.append(self.black.astype(np.float32))
        # proximity legal mask (shared baseline for placing/moving destinations)
        planes.append(self._adjacent_mask().astype(np.float32))
        # banned color one-hot (R,G,B,Y), tiled across board (Gray ban isn't a separate plane;
        # gray participation in ban is handled in action legality)
        banned = self.banned_colors()
        bvec = np.zeros(4, dtype=np.float32)
        for col in banned:
            if col in COLOR_TO_IDX:
                bvec[COLOR_TO_IDX[col]] = 1.0
        for i in range(4):
            planes.append(np.full_like(planes[0], bvec[i], dtype=np.float32))
        # parity plane
        planes.append(np.full_like(planes[0], 1.0 if self.player==+1 else -1.0, dtype=np.float32))
        # bias plane
        planes.append(np.ones_like(planes[0], dtype=np.float32))

        arr = np.stack(planes, axis=0)  # (C,H,W)
        return arr, self.player
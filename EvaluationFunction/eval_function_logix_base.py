# train_logix_value.py
# Self-play training for Logix-style shapes with assigned colors.
# Adds: place / move / replace actions, gray participates in color ban,
# per-player inventories (R,G,B,Y=6; Gray=2), and "no adjacent same-colored
# marbles" constraint around finished shape. Rotations only (no mirrors).
#
# Press ENTER to stop gracefully; checkpoints + ONNX export are saved periodically.

import os
import time
import random
import threading
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional, Iterable

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

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
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
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
torch.manual_seed(CFG.seed)
os.makedirs(CFG.ckpt_dir, exist_ok=True)

# ============================================================
# Environment with place / move / replace, bans, inventory, win check
# ============================================================

# Board encoding:
# 0 empty
# 1 R, 2 G, 3 B, 4 Y, 5 Gray, 9 Black
COLOR_CODE = {"R":1, "G":2, "B":3, "Y":4, "Gray":5}
IDX_TO_COLOR = {1:"R", 2:"G", 3:"B", 4:"Y", 5:"Gray"}

InventoryDict = Dict[str, int]

class LogixShapeEnv:
    def __init__(self, n=7, max_game_len=90):
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

        # Last color played (ban source) per player; now Gray also sets bans
        self.last_color_played: Dict[int, Optional[str]] = {+1: None, -1: None}

        # Per-player inventories
        def make_inv() -> InventoryDict:
            return {"R":6, "G":6, "B":6, "Y":6, "Gray":2}
        self.inventory: Dict[int, InventoryDict] = {+1: make_inv(), -1: make_inv()}

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

    def banned_color_for_current_player(self) -> Optional[str]:
        """Ban equals opponent's last color (including Gray)."""
        opp = -self.player
        return self.last_color_played[opp]

    def _is_blocked_piece(self, r: int, c: int) -> bool:
        """Blocked if all 4 neighbors are occupied (board or black)."""
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            rr, cc = r+dr, c+dc
            if self.inside(rr, cc) and self.board[rr, cc] == 0 and self.black[rr, cc] == 0:
                return False
        return True

    # ------------- Actions listing -------------

    def legal_moves(self) -> List[Tuple]:
        """
        Returns a list of *action tuples*:
          - ('place', r, c, color)
          - ('move', r1, c1, r2, c2)          # cannot move black; source must not be fully blocked
          - ('replace', r, c, color)          # replace board cell with a color from inventory
        All obey the banned-color rule (including Gray).
        Placement/move destinations must be adjacent to any occupied (proximity rule).
        """
        acts = []
        banned = self.banned_color_for_current_player()
        adj = self._adjacent_mask()

        inv = self.inventory[self.player]

        # --- PLACE: from inventory to empty adj cell ---
        for r in range(self.n):
            for c in range(self.n):
                if adj[r, c] != 1: continue
                if self.board[r, c] != 0: continue
                for col in ("R","G","B","Y","Gray"):
                    if col == banned: continue
                    if inv[col] <= 0: continue
                    acts.append(("place", r, c, col))

        # --- MOVE: move an existing non-black marble to empty adj cell ---
        for r1 in range(self.n):
            for c1 in range(self.n):
                v = self.board[r1, c1]
                if v == 0: continue
                if v == 9 or self.black[r1, c1] == 1: continue  # can't move black
                # require not fully blocked (simplified rule)
                if self._is_blocked_piece(r1, c1):
                    continue
                moved_color = IDX_TO_COLOR.get(v, "Gray") if v in (1,2,3,4) else "Gray"
                if moved_color == banned:
                    continue
                for r2 in range(self.n):
                    for c2 in range(self.n):
                        if self.board[r2, c2] != 0: continue
                        if adj[r2, c2] != 1: continue
                        acts.append(("move", r1, c1, r2, c2))

        # --- REPLACE: swap board cell with inventory color (no dest proximity check needed) ---
        for r in range(self.n):
            for c in range(self.n):
                v = self.board[r, c]
                if v == 0: continue
                if self.black[r, c] == 1: continue  # cannot replace black
                cur_color = IDX_TO_COLOR.get(v, "Gray") if v in (1,2,3,4) else "Gray"
                for col in ("R","G","B","Y","Gray"):
                    if col == banned: continue
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
        banned = self.banned_color_for_current_player()
        inv = self.inventory[self.player]

        if typ == "place":
            _, r, c, col = action
            assert self.board[r, c] == 0, "Illegal: occupied"
            assert self._adjacent_mask()[r, c] == 1, "Illegal: not adjacent for placement"
            assert col != banned, f"Illegal: color {col} is banned"
            assert inv[col] > 0, f"No inventory for {col}"
            self.board[r, c] = COLOR_CODE[col]
            inv[col] -= 1
            self.last_color_played[self.player] = col

        elif typ == "move":
            _, r1, c1, r2, c2 = action
            v = self.board[r1, c1]
            assert v != 0 and self.black[r1, c1] == 0, "Illegal: no piece or black at source"
            assert not self._is_blocked_piece(r1, c1), "Illegal: source piece is fully blocked"
            moved_color = IDX_TO_COLOR.get(v, "Gray") if v in (1,2,3,4) else "Gray"
            assert moved_color != banned, f"Illegal: color {moved_color} is banned"
            assert self.board[r2, c2] == 0, "Illegal: destination occupied"
            assert self._adjacent_mask()[r2, c2] == 1, "Illegal: destination not adjacent"
            # perform move
            self.board[r1, c1] = 0
            self.board[r2, c2] = v
            self.last_color_played[self.player] = moved_color

        elif typ == "replace":
            _, r, c, col = action
            v = self.board[r, c]
            assert v != 0 and self.black[r, c] == 0, "Illegal: cannot replace empty or black"
            cur_color = IDX_TO_COLOR.get(v, "Gray") if v in (1,2,3,4) else "Gray"
            assert col != cur_color, "Illegal: replacing by same color is pointless"
            assert col != banned, f"Illegal: color {col} is banned"
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
            self.last_color_played[self.player] = col

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
        new_env.center = self.center
        new_env.last_color_played = {+1: self.last_color_played[+1], -1: self.last_color_played[-1]}
        # deep copy inventories
        new_env.inventory = {
            +1: dict(self.inventory[+1]),
            -1: dict(self.inventory[-1]),
        }
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
        banned = self.banned_color_for_current_player()
        bvec = np.zeros(4, dtype=np.float32)
        if banned in COLOR_TO_IDX:
            bvec[COLOR_TO_IDX[banned]] = 1.0
        for i in range(4):
            planes.append(np.full_like(planes[0], bvec[i], dtype=np.float32))
        # parity plane
        planes.append(np.full_like(planes[0], 1.0 if self.player==+1 else -1.0, dtype=np.float32))
        # bias plane
        planes.append(np.ones_like(planes[0], dtype=np.float32))

        arr = np.stack(planes, axis=0)  # (C,H,W)
        return arr, self.player

# ============================================================
# Replay Buffer
# ============================================================

class Replay:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.X = []
        self.y = []
        self._len = 0

    def add_many(self, states: List[np.ndarray], targets: List[float]):
        for s, t in zip(states, targets):
            if self._len >= self.capacity:
                self.X.pop(0); self.y.pop(0); self._len -= 1
            self.X.append(s.astype(np.float32))
            self.y.append(float(t))
            self._len += 1

    def __len__(self):
        return self._len

    def sample(self, batch_size: int):
        idx = np.random.choice(self._len, size=batch_size, replace=False)
        Xb = np.stack([self.X[i] for i in idx], axis=0)
        yb = np.array([self.y[i] for i in idx], dtype=np.float32)
        return Xb, yb

# ============================================================
# Model
# ============================================================

class ValueNet(nn.Module):
    def __init__(self, in_planes=13, board=7):
        super().__init__()
        ch = 64
        self.conv1 = nn.Conv2d(in_planes, ch, 3, padding=1)
        self.conv2 = nn.Conv2d(ch, ch, 3, padding=1)
        self.conv3 = nn.Conv2d(ch, ch, 3, padding=1)
        self.head = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(ch, 128),
            nn.ReLU(),
            nn.Linear(128, 1),
            nn.Tanh(),
        )

    def forward(self, x):
        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))
        x = F.relu(self.conv3(x))
        v = self.head(x)
        return v.squeeze(1)

# ============================================================
# Self-play Agent (ε-greedy over lookahead value of actions)
# ============================================================

class Agent:
    def __init__(self, model: ValueNet, epsilon: float):
        self.model = model
        self.epsilon = epsilon

    @torch.no_grad()
    def select_move(self, env: LogixShapeEnv):
        actions = env.legal_moves()
        if not actions:
            return None
        if random.random() < self.epsilon:
            return random.choice(actions)

        best_score = -1e9
        best_act = actions[0]
        for act in actions:
            sim_env, done, res = env.simulate_move(act)
            planes, _ = sim_env._obs()
            X = torch.from_numpy(planes[None, ...]).to(CFG.device)
            v = self.model(X).item()
            if done:
                v = env.result_from_perspective(res, env.player)
            if v > best_score:
                best_score = v
                best_act = act
        return best_act

# ============================================================
# Training loop
# ============================================================

def anneal_epsilon(epi: int) -> float:
    a, b, T = CFG.epsilon_start, CFG.epsilon_end, CFG.epsilon_anneal_episodes
    if epi >= T: return b
    return a + (b - a) * (epi / T)

def self_play_episode(model: ValueNet, epsilon: float):
    env = LogixShapeEnv(CFG.board_size, CFG.max_game_len)
    agent = Agent(model, epsilon=epsilon)

    traj_states = []
    traj_players = []

    done = False
    result_abs = 0

    while not done:
        planes, player = env._obs()
        traj_states.append(planes)
        traj_players.append(player)

        act = agent.select_move(env)
        if act is None:
            done = True
            result_abs = 0
            break

        _, done, res = env.step(act)
        if done:
            result_abs = res

    targets = [env.result_from_perspective(result_abs, p) for p in traj_players]
    return traj_states, targets, result_abs, len(traj_states), env.objectives

def save_checkpoint(model: ValueNet, optimizer: torch.optim.Optimizer, steps: int):
    """Save timestamped .pt and .onnx under checkpoints/YYYY-MM-DD/."""
    day_dir = time.strftime("%Y-%m-%d")
    out_dir = os.path.join(CFG.ckpt_dir, day_dir)
    os.makedirs(out_dir, exist_ok=True)

    stamp = time.strftime("%Y%m%d_%H%M")  # e.g., 20251107_0140
    pt_path = os.path.join(out_dir, f"{stamp}_{CFG.model_name}")
    onnx_path = os.path.join(out_dir, f"{stamp}_{CFG.onnx_name}")

    torch.save({
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "steps": steps,
        "config": CFG.__dict__,
    }, pt_path)
    print(f"[checkpoint] saved: {pt_path}")

    dummy = torch.randn(1, CFG.in_planes, CFG.board_size, CFG.board_size, device=CFG.device)
    torch.onnx.export(model, dummy, onnx_path, input_names=["x"], output_names=["v"], opset_version=13)
    print(f"[onnx] exported: {onnx_path}")

def main():
    print(f"Device: {CFG.device}")
    model = ValueNet(CFG.in_planes, CFG.board_size).to(CFG.device)
    opt = torch.optim.Adam(model.parameters(), lr=CFG.lr)
    replay = Replay(CFG.replay_capacity)

    stop_event = threading.Event()
    def waiter():
        try:
            input("Running self-play (Logix shapes with place/move/replace & inventories). Press ENTER to stop…\n")
        except EOFError:
            pass
        stop_event.set()
    threading.Thread(target=waiter, daemon=True).start()

    last_save = time.time()
    episodes = 0
    train_steps = 0
    print("Starting self-play + training…")

    while not stop_event.is_set():
        epsilon = anneal_epsilon(episodes)
        states, targets, result_abs, moves, objectives = self_play_episode(model, epsilon=epsilon)
        replay.add_many(states, targets)
        episodes += 1

        if episodes % CFG.print_every_episodes == 0:
            p1 = objectives[+1]
            p2 = objectives[-1]

            p1txt = f"{p1[0]['shape'].name}/{p1[1]['shape'].name} | {p1[0]['assigned_color']},{p1[1]['assigned_color']}"
            p2txt = f"{p2[0]['shape'].name}/{p2[1]['shape'].name} | {p2[0]['assigned_color']},{p2[1]['assigned_color']}"

            # Compute a robust short-term win fraction for the latest game
            if moves and moves > 0:
                wr = sum(1 for t in targets[-moves:] if t > 0) / moves
            else:
                wr = float("nan")  # or 0.0 if you prefer

            print(
                f"[ep {episodes}] len={moves} last_result={result_abs:+d} ε={epsilon:.3f} "
                f"replay={len(replay)} p1=[{p1txt}] p2=[{p2txt}] sample_winfrac={wr:.2f}"
            )

        if len(replay) >= CFG.min_replay_to_train:
            Xb, yb = replay.sample(CFG.batch_size)
            X = torch.from_numpy(Xb).to(CFG.device)
            y = torch.from_numpy(yb).to(CFG.device)

            model.train()
            opt.zero_grad()
            v = model(X)
            y_clipped = torch.clamp(y, -CFG.value_clip, CFG.value_clip)
            loss = F.mse_loss(v, y_clipped)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            train_steps += 1

        if time.time() - last_save >= CFG.save_every_secs:
            save_checkpoint(model, opt, train_steps)
            last_save = time.time()

    save_checkpoint(model, opt, train_steps)
    print("Stopped. Final checkpoint saved.")

if __name__ == "__main__":
    main()

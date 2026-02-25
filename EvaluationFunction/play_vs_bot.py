# play_vs_bot.py
# Human vs greedy bot for the Logix env we've been training.
# - Loads the latest checkpoint under checkpoints/ (recursively)
# - Lets you input moves as text: place/move/replace
# - Bot uses greedy one-ply with the value net
#
# Usage:
#   python play_vs_bot.py
#
# Example inputs:
#   place 3 4 R
#   move 2 3 3 3
#   replace 2 2 Gray
#
# Board legend: . empty, K black, R/G/B/Y colors, * Gray

import os, re, glob, sys
import torch
import numpy as np

# Import your classes from your training file.
# If your file is named differently, adjust the import line below.
from eval_function_logix_base import ValueNet, CFG, LogixShapeEnv, IDX_TO_COLOR

# ---------- utils ----------

def find_latest_checkpoint_pt(root="checkpoints"):
    if not os.path.isdir(root):
        return None
    # search recursively for *.pt
    cands = [p for p in glob.glob(os.path.join(root, "**", "*.pt"), recursive=True) if os.path.isfile(p)]
    if not cands:
        return None
    cands.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return cands[0]

def load_model():
    model = ValueNet(CFG.in_planes, CFG.board_size)
    ckpt_path = find_latest_checkpoint_pt(CFG.ckpt_dir)
    if ckpt_path is None:
        print("[warn] No checkpoint found. Using randomly initialized model (bot will be weak).")
        return model.eval()
    ckpt = torch.load(ckpt_path, map_location="cpu")
    model.load_state_dict(ckpt["model"])
    model.eval()
    print(f"[ok] Loaded checkpoint: {ckpt_path}")
    return model

def encode_obs(env: LogixShapeEnv):
    obs, _ = env._obs()
    x = torch.from_numpy(obs).unsqueeze(0).float()
    return x

def value_of_next(model, env: LogixShapeEnv, act):
    # Simulate; if terminal, use true outcome from current player's perspective
    sim_env, done, res = env.simulate_move(act)
    if done:
        return float(env.result_from_perspective(res, env.player))
    with torch.no_grad():
        v = model(encode_obs(sim_env)).item()
    return float(v)

def pick_bot_move(model, env: LogixShapeEnv):
    actions = env.legal_moves()
    if not actions:
        return None, 0.0
    best_v, best_act = -1e9, actions[0]
    for a in actions:
        v = value_of_next(model, env, a)
        if v > best_v:
            best_v, best_act = v, a
    return best_act, best_v

def cell_char(v, is_black):
    if is_black:
        return "K"
    return {
        0: ".",
        1: "R",
        2: "G",
        3: "B",
        4: "Y",
        5: "*",
    }.get(v, "?")

def render(env: LogixShapeEnv):
    n = env.n
    # header
    print("\n   " + " ".join(str(c) for c in range(n)))
    for r in range(n):
        row = []
        for c in range(n):
            is_black = (env.black[r, c] == 1)
            row.append(cell_char(int(env.board[r,c]), is_black))
        print(f"{r:2d} " + " ".join(row))
    # inventories, bans, objectives preview
    banned = env.banned_color_for_current_player()
    inv_me = env.inventory[env.player]
    inv_opp = env.inventory[-env.player]
    def inv_str(inv): return f"R{inv['R']} G{inv['G']} B{inv['B']} Y{inv['Y']} Gray{inv['Gray']}"
    print(f"\nPlayer to move: {env.player:+d} | Banned color this turn: {banned}")
    print(f"My inventory:   {inv_str(inv_me)}")
    print(f"Opp inventory:  {inv_str(inv_opp)}")
    # two objectives per player (names + assigned colors)
    def obj_txt(objs):
        return f"{objs[0]['shape'].name}/{objs[1]['shape'].name} | assigned={objs[0]['assigned_color']},{objs[1]['assigned_color']}"
    print(f"P+1 objectives: {obj_txt(env.objectives[+1])}")
    print(f"P-1 objectives: {obj_txt(env.objectives[-1])}")

def parse_action(inp: str):
    """
    Accept lines like:
      place r c color
      move r1 c1 r2 c2
      replace r c color
    Colors: R,G,B,Y,Gray (case-insensitive).
    Returns a tuple matching env.step() formats or None if bad.
    """
    s = inp.strip().split()
    if not s:
        return None
    t = s[0].lower()
    if t == "place" and len(s) == 4:
        try:
            r = int(s[1]); c = int(s[2])
            col = s[3].capitalize()
            if col in ("R","G","B","Y","Gray"):
                return ("place", r, c, col)
        except:
            return None
    elif t == "move" and len(s) == 5:
        try:
            r1 = int(s[1]); c1 = int(s[2]); r2 = int(s[3]); c2 = int(s[4])
            return ("move", r1, c1, r2, c2)
        except:
            return None
    elif t == "replace" and len(s) == 4:
        try:
            r = int(s[1]); c = int(s[2])
            col = s[3].capitalize()
            if col in ("R","G","B","Y","Gray"):
                return ("replace", r, c, col)
        except:
            return None
    return None

def list_some_legal(env: LogixShapeEnv, limit=40):
    acts = env.legal_moves()
    if not acts:
        print("No legal actions.")
        return acts
    print(f"\nLegal actions (showing up to {limit} of {len(acts)}):")
    for i, a in enumerate(acts[:limit]):
        print(f"  [{i}] {a}")
    if len(acts) > limit:
        print("  ... (more not shown)")
    return acts

# ---------- main play loop ----------

def main():
    print("Loading model...")
    model = load_model()

    # Decide who moves first: human plays +1 by default; change here if you want.
    human_player = +1

    env = LogixShapeEnv(CFG.board_size, CFG.max_game_len)

    while True:
        # render board
        render(env)

        # check terminal by asking if current player already won after last move;
        # (env.step) handles this, but we also break when we see no legal actions.
        legal = env.legal_moves()
        if not legal:
            print("\nNo legal moves available. Game drawn.")
            break

        if env.player == human_player:
            # Human turn
            acts = list_some_legal(env, limit=40)
            print("\nYour move. Type one of:")
            print("  place r c color    e.g.,  place 3 4 R")
            print("  move r1 c1 r2 c2   e.g.,  move 2 3 3 3")
            print("  replace r c color  e.g.,  replace 1 1 Gray")
            print("Or type 'idx N' to select a listed action by index.")
            while True:
                try:
                    line = input("> ").strip()
                except EOFError:
                    print("\nInput closed. Exiting.")
                    return
                if not line:
                    continue
                if line.lower().startswith("idx "):
                    try:
                        k = int(line.split()[1])
                        if 0 <= k < len(acts):
                            act = acts[k]
                            break
                        else:
                            print("Index out of range.")
                            continue
                    except:
                        print("Bad idx syntax. Example: idx 5")
                        continue
                else:
                    act = parse_action(line)
                    if act is None:
                        print("Could not parse. Try again.")
                        continue
                    # quick legality check: ensure the exact action is legal
                    if act not in acts:
                        print("That action is not currently legal. Try listing with 'idx N' from above.")
                        continue
                    break

            try:
                _, done, res = env.step(act)
            except AssertionError as e:
                print(f"Illegal move: {e}")
                continue

            if done:
                render(env)
                if res == +1:
                    print("\nResult: Player +1 (human) WINS!")
                elif res == -1:
                    print("\nResult: Player -1 (bot) WINS!")
                else:
                    print("\nResult: Draw.")
                break

        else:
            # Bot turn (greedy)
            act, score = pick_bot_move(model, env)
            if act is None:
                print("\nBot has no legal moves. Game drawn.")
                break
            print(f"\nBot plays: {act} (predicted score {score:+.3f})")
            _, done, res = env.step(act)
            if done:
                render(env)
                if res == +1:
                    print("\nResult: Player +1 (human) WINS!")
                elif res == -1:
                    print("\nResult: Player -1 (bot) WINS!")
                else:
                    print("\nResult: Draw.")
                break

if __name__ == "__main__":
    main()

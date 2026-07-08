import random
import numpy as np
import torch
import math

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LOGIX_ROOT = REPO_ROOT / "EvaluationFunction" / "eval_func_v2"

print("LOGIX_ROOT =", LOGIX_ROOT)
print("exists =", LOGIX_ROOT.exists())

sys.path.insert(0, str(LOGIX_ROOT))

from logix_az.env_logix_helper import LogixShapeEnv, COLOR_CODE
from logix_az.env_logix import LogixEnv
from logix_az.net import LogixNet
from logix_az.mcts import MCTS
from logix_az.action_encoding import A, decode_action
from logix_az.state_encoding import encode_state
from logix_az.action_encoding import encode_action


class Bot:
    def choose_move(self, env: LogixShapeEnv):
        raise NotImplementedError


class RandomBot(Bot):
    def choose_move(self, env):
        return random.choice(env.legal_moves())

    
class HeuristicBot(Bot):
    def __init__(self, max_safety_checks=20):
        self.max_safety_checks = max_safety_checks

    def choose_move(self, env):
        legal = env.legal_moves()
        random.shuffle(legal)

        # 1. If I can win immediately, play it.
        for move in legal:
            test_env, done, result = env.simulate_move(move)
            if done and result == env.player:
                return move

        # 2. Score moves cheaply.
        scored = []
        for move in legal:
            test_env, done, result = env.simulate_move(move)

            if done:
                score = self.terminal_score(result, env.player)
            else:
                score = self.evaluate_position(test_env, env.player)

            scored.append((score, move, test_env))

        scored.sort(reverse=True, key=lambda x: x[0])

        # 3. Check only top N moves for immediate opponent win.
        checked = 0
        for score, move, test_env in scored:
            if checked >= self.max_safety_checks:
                return move

            checked += 1

            if not self.opponent_can_win_immediately(test_env):
                return move

        # 4. Fallback: best heuristic move.
        return scored[0][1]

    def opponent_can_win_immediately(self, env):
        opponent = env.player

        for opp_move in env.legal_moves():
            after_opp, done, result = env.simulate_move(opp_move)

            if done and result == opponent:
                return True

        return False

    def terminal_score(self, result, root_player):
        if result == root_player:
            return 1_000_000
        if result == -root_player:
            return -1_000_000
        return 0

    def evaluate_position(self, env, player):
        my_progress = self.shape_progress(env, player)
        opp_progress = self.shape_progress(env, -player)

        return (
            1000 * my_progress
            - 1200 * opp_progress
            + 2 * len(env.legal_moves())
        )

    def shape_progress(self, env, player):
        best = 0

        for obj in env.objectives[player]:
            shape = obj["shape"]
            assigned = obj["assigned_color"]

            for shp in self.rotations(shape):
                offsets = shp.offsets

                for black_offset in offsets:
                    cells = self.cells_with_black_anchor(env.center, offsets, black_offset)

                    if any(not env.inside(r, c) for r, c in cells):
                        continue

                    for color in ("R", "G", "B", "Y"):
                        if color == assigned:
                            continue

                        code = COLOR_CODE[color]
                        matched = 0
                        empty = 0
                        blocked_wrong = 0

                        for r, c in cells:
                            if env.black[r, c] == 1:
                                matched += 1
                            elif env.board[r, c] == code:
                                matched += 1
                            elif env.board[r, c] == COLOR_CODE["Gray"]:
                                matched += 1
                            elif env.board[r, c] == 0:
                                empty += 1
                            else:
                                blocked_wrong += 1

                        if blocked_wrong == 0:
                            # Bigger reward for almost-complete shapes.
                            score = matched * matched - empty
                            best = max(best, score)

        return best

    def rotations(self, shape):
        from logix_az.env_logix_helper import iter_rotations
        return iter_rotations(shape)

    def cells_with_black_anchor(self, center, offsets, black_offset):
        br, bc = center
        ar, ac = black_offset

        return [
            (br + dr - ar, bc + dc - ac)
            for dr, dc in offsets
        ]
    
class NeuralAlphaBetaBot(Bot):
    def __init__(self, checkpoint_path, depth=3, move_limit=8, device=None):
        self.depth = depth
        self.move_limit = move_limit
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        ckpt = torch.load(str(checkpoint_path), map_location=self.device)

        board_channels = ckpt.get("board_channels", 6)
        feat_dim = ckpt.get("feat_dim", 99)

        self.net = LogixNet(board_channels, feat_dim).to(self.device)
        self.net.load_state_dict(ckpt["state_dict"])
        self.net.eval()

        self.eval_cache = {}
        self.policy_cache = {}

        print(f"Loaded NeuralAlphaBetaBot checkpoint: {checkpoint_path}")
        print(f"Device: {self.device}, depth={self.depth}, move_limit={self.move_limit}")

    def choose_move(self, helper_env):
        wrapper = LogixEnv(n=helper_env.n, max_game_len=helper_env.max_game_len)

        root_state = wrapper._pack_state(helper_env)
        root_player = root_state.player

        legal = helper_env.legal_moves()
        if not legal:
            return None

        # Immediate win shortcut
        for move in legal:
            test_env, done, result = helper_env.simulate_move(move)
            if done and result == root_player:
                return move

        ordered_moves = self.ordered_moves(wrapper, root_state)

        best_move = ordered_moves[0]
        best_score = -math.inf

        alpha = -math.inf
        beta = math.inf

        for move in ordered_moves:
            next_state = wrapper.step(root_state, encode_action(move))

            score = self.alphabeta(
                wrapper,
                next_state,
                depth=self.depth - 1,
                alpha=alpha,
                beta=beta,
                root_player=root_player,
            )

            if score > best_score:
                best_score = score
                best_move = move

            alpha = max(alpha, best_score)

        return best_move

    def alphabeta(self, wrapper, state, depth, alpha, beta, root_player):
        if wrapper.is_terminal(state):
            return self.terminal_score(wrapper, state, root_player)

        if depth == 0:
            return self.evaluate_state(wrapper, state, root_player)

        maximizing = state.player == root_player
        ordered_moves = self.ordered_moves(wrapper, state)

        if not ordered_moves:
            return self.evaluate_state(wrapper, state, root_player)

        if maximizing:
            value = -math.inf

            for move in ordered_moves:
                next_state = wrapper.step(state, encode_action(move))

                score = self.alphabeta(
                    wrapper,
                    next_state,
                    depth - 1,
                    alpha,
                    beta,
                    root_player,
                )

                value = max(value, score)
                alpha = max(alpha, value)

                if alpha >= beta:
                    break

            return value

        else:
            value = math.inf

            for move in ordered_moves:
                next_state = wrapper.step(state, encode_action(move))

                score = self.alphabeta(
                    wrapper,
                    next_state,
                    depth - 1,
                    alpha,
                    beta,
                    root_player,
                )

                value = min(value, score)
                beta = min(beta, value)

                if alpha >= beta:
                    break

            return value

    def ordered_moves(self, wrapper, state):
        """
        Fast move ordering using the trained policy head.

        This is much faster than evaluating every child state separately.
        The policy already gives a score for every possible action.
        """
        helper = wrapper._unpack_state(state)
        legal = helper.legal_moves()

        if not legal:
            return []

        key = self.state_key(state)
        if key in self.policy_cache:
            policy_logits = self.policy_cache[key]
        else:
            with torch.no_grad():
                bp, feat = encode_state(state)
                bp = bp.unsqueeze(0).to(self.device)
                feat = feat.unsqueeze(0).to(self.device)

                policy_logits, _ = self.net(bp, feat)
                policy_logits = policy_logits[0].detach().cpu()

            self.policy_cache[key] = policy_logits

        scored = []

        for move in legal:
            action = encode_action(move)
            score = float(policy_logits[action])

            # tiny noise avoids deterministic ties
            score += random.random() * 0.000001

            scored.append((score, move))

        # Policy is from the perspective of state.player,
        # so higher policy score means "more promising for player to move".
        scored.sort(reverse=True, key=lambda x: x[0])

        return [move for _, move in scored[:self.move_limit]]

    def terminal_score(self, wrapper, state, root_player):
        """
        Converts terminal result to root player's perspective.
        Large values are used so alpha-beta always prefers forced wins.
        """
        z = wrapper.outcome(state)

        if state.player == root_player:
            return 1_000_000 * z
        else:
            return -1_000_000 * z

    @torch.no_grad()
    def evaluate_state(self, wrapper, state, root_player):
        """
        Uses trained value head.
        Cached so repeated positions are not evaluated again.
        """
        key = self.state_key(state)

        if key in self.eval_cache:
            value = self.eval_cache[key]
        else:
            bp, feat = encode_state(state)
            bp = bp.unsqueeze(0).to(self.device)
            feat = feat.unsqueeze(0).to(self.device)

            _, v = self.net(bp, feat)
            value = float(v.item())

            self.eval_cache[key] = value

        # Neural value is from perspective of state.player.
        if state.player == root_player:
            return value
        else:
            return -value

    def state_key(self, state):
        """
        Fully hashable key for caching.
        Converts nested lists, dicts, sets, numpy arrays, etc. into tuples/bytes.
        """

        def make_hashable(x):
            if hasattr(x, "tobytes"):
                return x.tobytes()

            if isinstance(x, dict):
                return tuple(sorted((make_hashable(k), make_hashable(v)) for k, v in x.items()))

            if isinstance(x, (list, tuple)):
                return tuple(make_hashable(v) for v in x)

            if isinstance(x, set):
                return tuple(sorted(make_hashable(v) for v in x))

            return x

        parts = []

        for name in [
            "board",
            "black",
            "banned",
            "inventory",
            "objectives",
            "cards",
        ]:
            if hasattr(state, name):
                parts.append(make_hashable(getattr(state, name)))

        parts.append(make_hashable(state.player))

        if hasattr(state, "turn"):
            parts.append(make_hashable(state.turn))

        return tuple(parts)


class MCTSBot(Bot):
    """
    Neural MCTS bot.

    Loads trained LogixNet from checkpoint and uses it inside MCTS.
    """

    def __init__(self, checkpoint_path, num_sims=500, device=None):
        import torch

        self.checkpoint_path = str(checkpoint_path)
        self.num_sims = num_sims
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        ckpt = torch.load(self.checkpoint_path, map_location=self.device)

        board_channels = ckpt.get("board_channels", 6)
        feat_dim = ckpt.get("feat_dim", 99)

        self.net = LogixNet(board_channels, feat_dim).to(self.device)
        self.net.load_state_dict(ckpt["state_dict"])
        self.net.eval()

        print(f"Loaded MCTS bot checkpoint: {self.checkpoint_path}")
        print(f"Device: {self.device}")

    def move_wins_immediately(self, helper_env, move):
        test_env, done, result = helper_env.simulate_move(move)
        return done and result == helper_env.player


    def move_allows_opponent_win(self, helper_env, move):
        test_env, done, result = helper_env.simulate_move(move)

        if done:
            return False

        opponent = test_env.player

        for opp_move in test_env.legal_moves():
            after_opp, opp_done, opp_result = test_env.simulate_move(opp_move)

            if opp_done and opp_result == opponent:
                return True

        return False

    def choose_move(self, helper_env):
        legal_moves = helper_env.legal_moves()

        if not legal_moves:
            raise ValueError("MCTSBot: no legal moves available")

        # 1. Immediate win
        for move in legal_moves:
            test_env, done, result = helper_env.simulate_move(move)
            if done and result == helper_env.player:
                return move

        # 2. Run neural MCTS
        wrapper = LogixEnv(
            n=helper_env.n,
            max_game_len=helper_env.max_game_len
        )

        state = wrapper._pack_state(helper_env)

        mcts = MCTS(
            wrapper,
            self.net,
            A,
            c_puct=1.5,
            device=self.device
        )

        visits = mcts.run(
            state,
            num_sims=self.num_sims,
            add_noise=False
        )

        legal_mask = wrapper.legal_actions_mask(state)
        visits[~legal_mask] = 0

        ranked_actions = np.argsort(visits)[::-1]

        # 3. Pick best MCTS move that does not allow opponent immediate win
        for action in ranked_actions:
            if visits[action] <= 0:
                break

            move = decode_action(int(action))

            if move not in legal_moves:
                continue

            test_env, done, result = helper_env.simulate_move(move)

            if done:
                return move

            opponent = test_env.player
            opponent_can_win = False

            for opp_move in test_env.legal_moves():
                after_opp, opp_done, opp_result = test_env.simulate_move(opp_move)

                if opp_done and opp_result == opponent:
                    opponent_can_win = True
                    break

            if not opponent_can_win:
                return move

        # 4. Fallback: best legal MCTS move, even if unsafe
        for action in ranked_actions:
            move = decode_action(int(action))
            if move in legal_moves:
                return move

        # 5. Last fallback
        return random.choice(legal_moves)
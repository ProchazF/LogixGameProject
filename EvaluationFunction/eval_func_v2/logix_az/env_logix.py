from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import numpy as np

from .action_encoding import A, decode_action, encode_action
from .env_logix_helper import LogixShapeEnv

COLOR_ORDER = ("R", "G", "B", "Y", "Gray")
COLOR_TO_BANNED_IDX = {c: i for i, c in enumerate(COLOR_ORDER)}


@dataclass(frozen=True)
class LogixState:
    """
    Immutable snapshot of the helper environment.

    board encoding:
      0 = empty
      1 = R
      2 = G
      3 = B
      4 = Y
      5 = Gray
      9 = Black
    """
    board: np.ndarray          # shape (7,7), black encoded as 9
    player: int                # +1 or -1
    turn: int
    banned: np.ndarray         # shape (5,) bool for [R,G,B,Y,Gray]
    inventory: np.ndarray      # shape (5,) counts for [R,G,B,Y,Gray]
    objectives: Any

    @property
    def banned_mask(self) -> np.ndarray:
        return self.banned


class LogixEnv:
    def __init__(self, seed: int | None = None, n: int = 7, max_game_len: int = 100):
        self.rng = np.random.default_rng(seed)
        self.n = n
        self.max_game_len = max_game_len

    # --------------------------------------------------
    # helper <-> immutable state conversion
    # --------------------------------------------------

    def _pack_state(self, env: LogixShapeEnv) -> LogixState:
        """
        Convert helper env into immutable LogixState.
        """
        board = env.board.copy().astype(np.int8)

        # encode black into the board as 9
        board[env.black == 1] = 9

        banned = np.zeros((5,), dtype=bool)
        for col in env.banned_colors():
            if col in COLOR_TO_BANNED_IDX:
                banned[COLOR_TO_BANNED_IDX[col]] = True

        inventory = np.array([env.inventory[c] for c in COLOR_ORDER], dtype=np.int16)

        return LogixState(
            board=board,
            player=int(env.player),
            turn=int(env.turn),
            banned=banned,
            inventory=inventory,
            objectives=env.objectives,
        )

    def _unpack_state(self, state: LogixState) -> LogixShapeEnv:
        """
        Rebuild helper env from immutable LogixState.
        """
        env = LogixShapeEnv(n=self.n, max_game_len=self.max_game_len)

        # restore board and black layer
        env.board = state.board.copy().astype(np.int8)
        env.black = (env.board == 9).astype(np.int8)
        env.board[env.board == 9] = 0

        env.player = int(state.player)
        env.turn = int(state.turn)

        # find black center
        black_positions = np.argwhere(env.black == 1)
        if len(black_positions) != 1:
            raise ValueError("State must contain exactly one black marble.")
        env.center = tuple(black_positions[0])

        # restore global banned colors
        env.last_colors_played = {
            COLOR_ORDER[i] for i in range(len(COLOR_ORDER)) if state.banned[i]
        }

        # restore shared inventory
        env.inventory = {
            COLOR_ORDER[i]: int(state.inventory[i])
            for i in range(len(COLOR_ORDER))
        }

        # restore objectives
        env.objectives = state.objectives

        return env

    # --------------------------------------------------
    # environment API used by training / MCTS
    # --------------------------------------------------

    def reset(self) -> LogixState:
        env = LogixShapeEnv(n=self.n, max_game_len=self.max_game_len)
        env.reset()
        return self._pack_state(env)

    def legal_actions_mask(self, state: LogixState) -> np.ndarray:
        env = self._unpack_state(state)
        moves = env.legal_moves()

        mask = np.zeros((A,), dtype=bool)
        for mv in moves:
            a = encode_action(mv)
            mask[a] = True

        return mask

    def step(self, state: LogixState, action: int) -> LogixState:
        env = self._unpack_state(state)
        move = decode_action(action)
        env.step(move)
        return self._pack_state(env)

    def is_terminal(self, state: LogixState) -> bool:
        env = self._unpack_state(state)

        if env.turn >= env.max_game_len:
            return True

        # In helper.step(), if a player wins, player is not flipped.
        # So terminal state means current player has the winning shape.
        if env._check_win_for_player(env.player):
            return True

        return False

    def outcome(self, state: LogixState) -> float:
        """
        Return terminal outcome from the perspective of the player-to-move
        in THIS state.
        """
        env = self._unpack_state(state)

        if env._check_win_for_player(env.player):
            return 1.0

        if env.turn >= env.max_game_len:
            return 0.0

        raise ValueError("outcome() called on a non-terminal state")

    def canonicalize(self, state: LogixState) -> LogixState:
        """
        For now, leave state unchanged.
        Later you can make this player-relative if needed.
        """
        return state

    def symmetries(self, state, pi):
        """
        Rotations only, no mirror.
        Stub for now.
        """
        return [(state, pi)]
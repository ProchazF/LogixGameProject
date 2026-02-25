# env_logix.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any, Tuple
import numpy as np

from .action_encoding import A, decode_action
from .env_logix_helper import LogixShapeEnv

# Keep these consistent helper env
COLOR_ORDER = ("R", "G", "B", "Y", "Gray")
COLOR_TO_BANNED_IDX = {c: i for i, c in enumerate(COLOR_ORDER)}

@dataclass(frozen=True)
class LogixState:
    """
    Minimal immutable snapshot of the helper environment.
    """
    board: np.ndarray                  # (7,7) int8, with black encoded as 9
    player: int                        # +1 or -1 (same as helper)
    turn: int
    last_color_p1: Optional[str]       # last color played by +1
    last_color_p2: Optional[str]       # last color played by -1
    inv_p1: np.ndarray                 # (5,) counts for +1 in COLOR_ORDER
    inv_p2: np.ndarray                 # (5,) counts for -1 in COLOR_ORDER
    objectives: Any                    # whatever helper uses; should be picklable (dict with WinShape, strings, tuples)

    @property
    def banned_mask(self) -> np.ndarray:
        """
        Bool mask (5,) for [R,G,B,Y,Gray] banned for CURRENT player.
        Rule in helper: banned = opponent's last color (including Gray).
        """
        opp_last = self.last_color_p2 if self.player == +1 else self.last_color_p1
        mask = np.zeros((len(COLOR_ORDER),), dtype=bool)
        if opp_last is not None and opp_last in COLOR_TO_BANNED_IDX:
            mask[COLOR_TO_BANNED_IDX[opp_last]] = True
        return mask


class LogixEnv:
    def __init__(self, seed: int | None = None, n: int = 7, max_game_len: int = 90):
        self.rng = np.random.default_rng(seed)
        self.n = n
        self.max_game_len = max_game_len

    def reset(self) -> LogixState:
        # returns gam,e board
        raise NotImplementedError

    def legal_actions_mask(self, state: LogixState) -> np.ndarray:
        # returns bool mask of length A
        raise NotImplementedError

    def step(self, state: LogixState, action: int) -> LogixState:
        # apply decoded action, return new state
        raise NotImplementedError

    def is_terminal(self, state: LogixState) -> bool:
        raise NotImplementedError

    def outcome(self, state: LogixState) -> float:
        """
        Return z in {-1, 0, +1} from the perspective of the player-to-move
        for the *terminal* state.
        """
        raise NotImplementedError

    def canonicalize(self, state: LogixState) -> LogixState:
        """
        Optional: convert to 'current player' perspective so the net only
        sees one viewpoint.
        """
        return state

    def symmetries(self, state, pi):
        """
        Return rotated versions of (state, pi). Rotations only, no mirror.
        """
        return [(state, pi)]
import numpy as np
import torch

COLOR_ORDER = ("R", "G", "B", "Y", "Gray")
COLOR_TO_IDX = {c: i for i, c in enumerate(COLOR_ORDER)}

# Build a stable shape-name vocabulary.
# These names must match the names used by WinShape in env_logix_helper.py.
SHAPE_NAMES = [
    "Line",
    "Plus",
    "T-Shape",
    "Long L-Shape Mirrored",
    "Long L-Shape",
    "Short L-Shape",
    "Seven-Shape",
    "Mirrored Seven-Shape",
    "C-Shape",
    "Stair-Shape",
    "Z-Shape",
    "Reverse Z-Shape",
    "One-Shape",
    "Reverse One-Shape",
    "d-shape",
    "b-shape",
    "Snake",
    "Reverse Snake",
]

SHAPE_TO_IDX = {name: i for i, name in enumerate(SHAPE_NAMES)}


def _base_shape_name(shape_name: str) -> str:
    """
    Helper shapes may have names like 'Line@90'.
    Strip rotation suffix so all rotations map to the same base shape id.
    """
    return shape_name.split("@")[0]


def _encode_objectives(objectives) -> np.ndarray:
    """
    Encodes the helper objectives dict into a flat numeric feature vector.

    Expected structure:
      {
        +1: [{"shape": WinShape(...), "assigned_color": "R", ...}, {...}],
        -1: [{"shape": WinShape(...), "assigned_color": "G", ...}, {...}],
      }

    For each of the 4 objectives:
      - one-hot shape id (18 dims)
      - one-hot assigned color among R,G,B,Y (4 dims)

    Total = 4 * (18 + 4) = 88 dims
    """
    feat = []

    for who in (+1, -1):
        objs = objectives[who]
        for obj in objs:
            shape = obj["shape"]
            assigned = obj["assigned_color"]

            base_name = _base_shape_name(shape.name)

            shape_onehot = np.zeros(len(SHAPE_NAMES), dtype=np.float32)
            if base_name in SHAPE_TO_IDX:
                shape_onehot[SHAPE_TO_IDX[base_name]] = 1.0

            assigned_onehot = np.zeros(4, dtype=np.float32)
            if assigned in ("R", "G", "B", "Y"):
                assigned_onehot[("R", "G", "B", "Y").index(assigned)] = 1.0

            feat.append(shape_onehot)
            feat.append(assigned_onehot)

    if len(feat) == 0:
        return np.zeros((0,), dtype=np.float32)

    return np.concatenate(feat, axis=0)


def encode_state(state) -> tuple[torch.Tensor, torch.Tensor]:
    """
    Returns:
      board_planes: (C, 7, 7) float32
      features:     (F,) float32

    Current encoding:
      Board planes (6):
        0: R
        1: G
        2: B
        3: Y
        4: Gray
        5: Black

      Feature vector:
        - banned colors (5)
        - shared inventory (5)
        - current player (1)
        - encoded objectives (88)
    """
    board = state.board  # values: 0 empty, 1..5 colors, 9 black

    planes = [
        (board == 1).astype(np.float32),  # R
        (board == 2).astype(np.float32),  # G
        (board == 3).astype(np.float32),  # B
        (board == 4).astype(np.float32),  # Y
        (board == 5).astype(np.float32),  # Gray
        (board == 9).astype(np.float32),  # Black
    ]

    board_planes = np.stack(planes, axis=0)  # (6,7,7)

    banned_feat = state.banned.astype(np.float32)         # (5,)
    inventory_feat = state.inventory.astype(np.float32)   # (5,)
    player_feat = np.array([float(state.player)], dtype=np.float32)  # (1,)
    objective_feat = _encode_objectives(state.objectives)            # (88,)

    features = np.concatenate(
        [banned_feat, inventory_feat, player_feat, objective_feat],
        axis=0
    )

    return torch.from_numpy(board_planes), torch.from_numpy(features)
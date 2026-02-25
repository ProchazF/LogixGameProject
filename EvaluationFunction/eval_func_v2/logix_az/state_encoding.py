#  state_encoding.py
import numpy as np
import torch

def encode_state(state) -> tuple[torch.Tensor, torch.Tensor]:
    """
    Returns:
      board_planes: (C, 7, 7) float32
      features:     (F,) float32  (cards, inventories, etc.)
    """
    board = state.board  # (7,7) int codes
    # Example: 6 board planes: R,G,B,Y,Gray,Black
    planes = []
    for code in range(6):
        planes.append((board == code).astype(np.float32))
    # banned color planes (optional)
    # planes.append( ... broadcast ... )

    board_planes = np.stack(planes, axis=0)  # (C,7,7)
    features = np.concatenate([
        state.banned.astype(np.float32),
        state.cards.astype(np.float32),
        state.inv.reshape(-1).astype(np.float32),
    ], axis=0)

    return torch.from_numpy(board_planes), torch.from_numpy(features)
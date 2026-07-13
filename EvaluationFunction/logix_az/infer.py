# infer.py
import numpy as np
import torch
from .net import LogixNet
from .state_encoding import encode_state
from .action_encoding import A

class LogixEvaluator:
    def __init__(self, ckpt_path: str, board_channels: int, feat_dim: int, device="cpu"):
        self.device = device
        self.net = LogixNet(board_channels, feat_dim).to(device)
        ckpt = torch.load(ckpt_path, map_location=device)
        self.net.load_state_dict(ckpt["state_dict"])
        self.net.eval()

    @torch.no_grad()
    def evaluate(self, state, legal_mask: np.ndarray):
        bp, ft = encode_state(state)
        bp = bp.unsqueeze(0).to(self.device)
        ft = ft.unsqueeze(0).to(self.device)
        logits, v = self.net(bp, ft)
        logits = logits.squeeze(0).cpu().numpy()
        v = float(v.item())

        # mask illegal actions and softmax
        x = logits.copy()
        x[~legal_mask] = -1e9
        x = x - x.max()
        p = np.exp(x)
        p[~legal_mask] = 0.0
        p = p / (p.sum() + 1e-8)

        return p, v
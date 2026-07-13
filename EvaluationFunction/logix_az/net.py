# net.py
import torch
import torch.nn as nn
import torch.nn.functional as F
from .action_encoding import A

class LogixNet(nn.Module):
    def __init__(self, board_channels: int, feat_dim: int, hidden: int = 128):
        super().__init__()
        self.conv1 = nn.Conv2d(board_channels, hidden, 3, padding=1)
        self.conv2 = nn.Conv2d(hidden, hidden, 3, padding=1)

        self.feat_fc = nn.Linear(feat_dim, hidden)

        self.policy_fc = nn.Linear(hidden + hidden, A)
        self.value_fc1 = nn.Linear(hidden + hidden, hidden)
        self.value_fc2 = nn.Linear(hidden, 1)

    def forward(self, board_planes, features):
        # board_planes: (B,C,7,7), features: (B,F)
        x = F.relu(self.conv1(board_planes))
        x = F.relu(self.conv2(x))
        x = x.mean(dim=(2,3))             # global average pool -> (B,hidden)

        f = F.relu(self.feat_fc(features)) # (B,hidden)

        h = torch.cat([x, f], dim=1)      # (B,2hidden)

        policy_logits = self.policy_fc(h) # (B,A)
        v = torch.tanh(self.value_fc2(F.relu(self.value_fc1(h)))).squeeze(1) # (B,)
        return policy_logits, v
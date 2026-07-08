import torch
import torch.nn as nn
import torch.nn.functional as F


class LogixNet(nn.Module):
    def __init__(self, board_channels=6, feat_dim=99, action_dim=2891):
        super().__init__()

        self.conv1 = nn.Conv2d(board_channels, 128, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(128, 128, kernel_size=3, padding=1)

        self.feat_fc = nn.Linear(feat_dim, 128)

        self.policy_fc = nn.Linear(256, action_dim)

        self.value_fc1 = nn.Linear(256, 128)
        self.value_fc2 = nn.Linear(128, 1)

    def forward(self, board, features):
        x = F.relu(self.conv1(board))
        x = F.relu(self.conv2(x))

        x = x.mean(dim=(2, 3))   # global average pooling

        f = F.relu(self.feat_fc(features))

        h = torch.cat([x, f], dim=1)

        policy = self.policy_fc(h)
        value = torch.tanh(self.value_fc1(h))
        value = torch.tanh(self.value_fc2(value))

        return policy, value


ckpt_path = "checkpoints/net_015200.pt"
onnx_path = "onnx/logix_net.onnx"

ckpt = torch.load(ckpt_path, map_location="cpu")

model = LogixNet(
    board_channels=ckpt["board_channels"],
    feat_dim=ckpt["feat_dim"],
    action_dim=2891
)

model.load_state_dict(ckpt["state_dict"])
model.eval()

dummy_board = torch.randn(1, 6, 7, 7)
dummy_features = torch.randn(1, 99)

torch.onnx.export(
    model,
    (dummy_board, dummy_features),
    onnx_path,
    input_names=["board", "features"],
    output_names=["policy", "value"],
    opset_version=17,
    dynamo=False
)

print(f"Exported to {onnx_path}")
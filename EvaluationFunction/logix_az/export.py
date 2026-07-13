# export.py
# export to ONNX for Unity
import torch
from .net import LogixNet
from .action_encoding import A

def export_onnx(pt_path: str, onnx_path: str, board_channels: int, feat_dim: int):
    net = LogixNet(board_channels, feat_dim)
    ckpt = torch.load(pt_path, map_location="cpu")
    net.load_state_dict(ckpt["state_dict"])
    net.eval()

    dummy_board = torch.zeros(1, board_channels, 7, 7)
    dummy_feat  = torch.zeros(1, feat_dim)

    torch.onnx.export(
        net,
        (dummy_board, dummy_feat),
        onnx_path,
        input_names=["board", "feat"],
        output_names=["policy_logits", "value"],
        opset_version=17,
        dynamic_axes={"board": {0: "batch"}, "feat": {0: "batch"}}
    )
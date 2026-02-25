# train.py
import os
import numpy as np
import torch
import torch.nn.functional as F
from torch import optim

from logix_az.env_logix import LogixEnv
from logix_az.net import LogixNet
from logix_az.mcts import MCTS
from logix_az.replay_buffer import ReplayBuffer
from logix_az.state_encoding import encode_state
from logix_az.action_encoding import A

def batch_encode(batch, device):
    boards, feats, pis, zs = [], [], [], []
    for s, pi, z in batch:
        bp, ft = encode_state(s)
        boards.append(bp)
        feats.append(ft)
        pis.append(torch.from_numpy(pi).float())
        zs.append(torch.tensor(z).float())
    boards = torch.stack(boards).to(device)  # (B,C,7,7)
    feats  = torch.stack(feats).to(device)   # (B,F)
    pis    = torch.stack(pis).to(device)     # (B,A)
    zs     = torch.stack(zs).to(device)      # (B,)
    return boards, feats, pis, zs

def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"

    env = LogixEnv(seed=0)

    # You’ll know these once state encoding is finalized:
    board_channels = 6  # example
    feat_dim = 5 + 4 + 12  # example placeholder

    net = LogixNet(board_channels, feat_dim).to(device)
    opt = optim.Adam(net.parameters(), lr=1e-3, weight_decay=1e-4)

    buffer = ReplayBuffer(max_size=200_000)

    os.makedirs("checkpoints", exist_ok=True)

    for iteration in range(1_000_000):
        # --- Self-play (can be parallelized later) ---
        mcts = MCTS(env, net, A, c_puct=1.5, device=device)
        from logix_az.selfplay import play_one_game
        examples = play_one_game(env, mcts, num_sims=200, tau_moves=10)
        buffer.add_game(examples)

        if len(buffer) < 2_000:
            continue

        # --- Train ---
        net.train()
        for step in range(200):  # training steps per iteration
            batch = buffer.sample(batch_size=64)
            boards, feats, target_pi, target_z = batch_encode(batch, device)

            logits, v = net(boards, feats)

            # policy loss: cross-entropy with soft targets (pi)
            logp = F.log_softmax(logits, dim=1)
            policy_loss = -(target_pi * logp).sum(dim=1).mean()

            value_loss = F.mse_loss(v, target_z)

            loss = policy_loss + value_loss

            opt.zero_grad()
            loss.backward()
            opt.step()

        net.eval()

        # --- Save checkpoint periodically ---
        if iteration % 50 == 0:
            path = f"checkpoints/net_{iteration:06d}.pt"
            torch.save({"iter": iteration, "state_dict": net.state_dict()}, path)
            print("saved", path)

if __name__ == "__main__":
    main()
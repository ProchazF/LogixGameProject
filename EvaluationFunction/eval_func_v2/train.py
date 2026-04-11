import os
import random
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
from logix_az.selfplay import play_one_game


def batch_encode(batch, device):
    boards, feats, pis, zs = [], [], [], []

    for s, pi, z in batch:
        bp, ft = encode_state(s)
        boards.append(bp)
        feats.append(ft)
        pis.append(torch.from_numpy(pi).float())
        zs.append(torch.tensor(z).float())

    boards = torch.stack(boards).to(device)   # (B,C,7,7)
    feats = torch.stack(feats).to(device)     # (B,F)
    pis = torch.stack(pis).to(device)         # (B,A)
    zs = torch.stack(zs).to(device)           # (B,)

    return boards, feats, pis, zs


def main():
    seed = 0
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("using device:", device)

    env = LogixEnv(seed=seed)

    # Must match state_encoding.py
    board_channels = 6
    feat_dim = 99

    net = LogixNet(board_channels, feat_dim).to(device)
    opt = optim.Adam(net.parameters(), lr=1e-3, weight_decay=1e-4)

    buffer = ReplayBuffer(max_size=200_000)

    os.makedirs("checkpoints", exist_ok=True)

    # original values
    # num_iterations = 1_000_000
    # num_sims = 200
    # tau_moves = 10
    # min_buffer_to_train = 2_000
    # train_steps_per_iteration = 200
    # batch_size = 64

    # mid values
    num_iterations = 1_000_000
    num_sims = 50
    tau_moves = 10
    min_buffer_to_train = 500
    train_steps_per_iteration = 50
    batch_size = 64

    # test values
    num_iterations = 10
    num_sims = 25
    tau_moves = 10
    train_steps_per_iteration = 10
    min_buffer_to_train = 10
    batch_size = 10

    for iteration in range(num_iterations):
        # ------------------------------
        # Self-play
        # ------------------------------
        net.eval()
        mcts = MCTS(env, net, A, c_puct=1.5, device=device)
        examples = play_one_game(env, mcts, num_sims=num_sims, tau_moves=tau_moves)
        buffer.add_game(examples)

        print(
            f"iter={iteration}  "
            f"game_examples={len(examples)}  "
            f"buffer={len(buffer)}"
        )

        if len(buffer) < min_buffer_to_train:
            continue

        # ------------------------------
        # Train
        # ------------------------------
        net.train()

        avg_loss = 0.0
        avg_policy_loss = 0.0
        avg_value_loss = 0.0

        for _ in range(train_steps_per_iteration):
            batch = buffer.sample(batch_size=batch_size)
            boards, feats, target_pi, target_z = batch_encode(batch, device)

            logits, v = net(boards, feats)

            if not torch.isfinite(logits).all():
                raise ValueError("NaN or Inf detected in policy logits during training.")
            if not torch.isfinite(v).all():
                raise ValueError("NaN or Inf detected in value head during training.")

            # policy loss: cross-entropy with soft targets
            logp = F.log_softmax(logits, dim=1)
            policy_loss = -(target_pi * logp).sum(dim=1).mean()

            # value loss
            value_loss = F.mse_loss(v, target_z)

            loss = policy_loss + value_loss

            opt.zero_grad()
            
            if not torch.isfinite(loss):
                raise ValueError("NaN or Inf detected in total loss.")

            loss.backward()
            opt.step()

            avg_loss += float(loss.item())
            avg_policy_loss += float(policy_loss.item())
            avg_value_loss += float(value_loss.item())

        avg_loss /= train_steps_per_iteration
        avg_policy_loss /= train_steps_per_iteration
        avg_value_loss /= train_steps_per_iteration

        print(
            f"train loss={avg_loss:.4f}  "
            f"policy={avg_policy_loss:.4f}  "
            f"value={avg_value_loss:.4f}"
        )

        # ------------------------------
        # Save checkpoint periodically
        # ------------------------------
        if iteration % 50 == 0:
            path = f"checkpoints/net_{iteration:06d}.pt"
            torch.save(
                {
                    "iter": iteration,
                    "state_dict": net.state_dict(),
                    "optimizer_state_dict": opt.state_dict(),
                    "board_channels": board_channels,
                    "feat_dim": feat_dim,
                },
                path,
            )
            print("saved", path)


if __name__ == "__main__":
    main()
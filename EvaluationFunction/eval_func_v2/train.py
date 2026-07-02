

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
from logix_az.human_loader import load_recorded_games


def log(msg, log_path, also_print=False):
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(str(msg) + "\n")

    if also_print:
        print(msg)


def batch_encode(batch, device):
    boards, feats, pis, zs = [], [], [], []

    for s, pi, z in batch:
        bp, ft = encode_state(s)
        boards.append(bp)
        feats.append(ft)
        pis.append(torch.from_numpy(pi).float())
        zs.append(torch.tensor(z).float())

    boards = torch.stack(boards).to(device)
    feats = torch.stack(feats).to(device)
    pis = torch.stack(pis).to(device)
    zs = torch.stack(zs).to(device)

    return boards, feats, pis, zs


def main():
    # ------------------------------
    # Config
    # ------------------------------
    seed = 0

    board_channels = 6
    feat_dim = 99

    # original values
    # num_iterations = 1_000_000
    # num_sims = 200
    # tau_moves = 10
    # min_buffer_to_train = 2_000
    # train_steps_per_iteration = 200
    # batch_size = 64

    # mid values
    num_iterations = 1_000_000
    num_sims = 25
    tau_moves = 10
    min_buffer_to_train = 500
    train_steps_per_iteration = 30
    batch_size = 64

    # test values
    # num_iterations = 10
    # num_sims = 25
    # tau_moves = 10
    # train_steps_per_iteration = 10
    # min_buffer_to_train = 10
    # batch_size = 10

    pretrain_steps = 1000

    checkpoint_dir = "checkpoints"
    log_path = "training_log.txt"

    # Set this to None to start from scratch.
    # Example:
    # resume_path = "checkpoints/net_000100.pt"
    resume_path = "checkpoints/net_015000.pt"

    # If False, writes only to training_log.txt.
    also_print = True

    # ------------------------------
    # Setup
    # ------------------------------
    os.makedirs(checkpoint_dir, exist_ok=True)

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    log("=" * 80, log_path, also_print)
    log("Starting training run", log_path, also_print)
    log(f"using device: {device}", log_path, also_print)

    env = LogixEnv(seed=seed)

    net = LogixNet(board_channels, feat_dim).to(device)
    opt = optim.Adam(net.parameters(), lr=1e-3, weight_decay=1e-4)

    start_iteration = 0

    # ------------------------------
    # Resume checkpoint if requested
    # ------------------------------
    if resume_path is not None:
        if not os.path.exists(resume_path):
            raise FileNotFoundError(f"resume_path does not exist: {resume_path}")

        ckpt = torch.load(resume_path, map_location=device)

        net.load_state_dict(ckpt["state_dict"])

        if "optimizer_state_dict" in ckpt:
            opt.load_state_dict(ckpt["optimizer_state_dict"])

        start_iteration = int(ckpt.get("iter", 0)) + 1

        log(
            f"Resumed from {resume_path}; starting at iteration {start_iteration}",
            log_path,
            also_print,
        )

    # ------------------------------
    # Replay buffer + human games
    # ------------------------------
    buffer = ReplayBuffer(max_size=200_000)

    human_examples = load_recorded_games("recorded_games")
    buffer.add_game(human_examples)

    log(
        f"Human examples added to replay buffer: {len(human_examples)}",
        log_path,
        also_print,
    )

    # ------------------------------
    # Human pretraining only when starting from scratch
    # ------------------------------
    if start_iteration == 0 and len(human_examples) > 0 and pretrain_steps > 0:
        log("Pretraining on human games...", log_path, also_print)

        net.train()

        for step in range(pretrain_steps):
            batch = random.sample(human_examples, min(batch_size, len(human_examples)))
            boards, feats, target_pi, target_z = batch_encode(batch, device)

            logits, v = net(boards, feats)

            logp = F.log_softmax(logits, dim=1)
            policy_loss = -(target_pi * logp).sum(dim=1).mean()
            value_loss = F.mse_loss(v, target_z)

            loss = policy_loss + value_loss

            opt.zero_grad()

            if not torch.isfinite(loss):
                raise ValueError("NaN or Inf detected during human pretraining.")

            loss.backward()
            opt.step()

            if step % 100 == 0:
                log(
                    f"pretrain step={step} "
                    f"loss={loss.item():.4f} "
                    f"policy={policy_loss.item():.4f} "
                    f"value={value_loss.item():.4f}",
                    log_path,
                    also_print,
                )

        net.eval()

    elif start_iteration > 0:
        log("Skipping human pretraining because training was resumed.", log_path, also_print)

    else:
        log("Skipping human pretraining because no human examples were loaded.", log_path, also_print)

    # ------------------------------
    # Main training loop
    # ------------------------------
    for iteration in range(start_iteration, num_iterations):
        # Self-play
        net.eval()

        log(f"starting self-play iteration {iteration}", log_path, also_print)

        mcts = MCTS(env, net, A, c_puct=1.5, device=device)
        examples = play_one_game(env, mcts, num_sims=num_sims, tau_moves=tau_moves)
        buffer.add_game(examples)

        log(
            f"iter={iteration} "
            f"game_examples={len(examples)} "
            f"buffer={len(buffer)}",
            log_path,
            also_print,
        )

        if len(buffer) < min_buffer_to_train:
            continue

        # Train
        net.train()

        avg_loss = 0.0
        avg_policy_loss = 0.0
        avg_value_loss = 0.0

        for _ in range(train_steps_per_iteration):
            human_n = min(batch_size // 2, len(human_examples))
            human_part = random.sample(human_examples, human_n)
            self_part = buffer.sample(batch_size=batch_size - human_n)
            batch = human_part + self_part
            boards, feats, target_pi, target_z = batch_encode(batch, device)

            logits, v = net(boards, feats)

            if not torch.isfinite(logits).all():
                raise ValueError("NaN or Inf detected in policy logits during training.")
            if not torch.isfinite(v).all():
                raise ValueError("NaN or Inf detected in value head during training.")

            logp = F.log_softmax(logits, dim=1)
            policy_loss = -(target_pi * logp).sum(dim=1).mean()
            value_loss = F.mse_loss(v, target_z)

            loss = policy_loss + value_loss

            if not torch.isfinite(loss):
                raise ValueError("NaN or Inf detected in total loss.")

            opt.zero_grad()
            loss.backward()
            opt.step()

            avg_loss += float(loss.item())
            avg_policy_loss += float(policy_loss.item())
            avg_value_loss += float(value_loss.item())

        avg_loss /= train_steps_per_iteration
        avg_policy_loss /= train_steps_per_iteration
        avg_value_loss /= train_steps_per_iteration

        log(
            f"train loss={avg_loss:.4f} "
            f"policy={avg_policy_loss:.4f} "
            f"value={avg_value_loss:.4f}",
            log_path,
            also_print,
        )

        # Save checkpoint
        if iteration % 50 == 0:
            path = os.path.join(checkpoint_dir, f"net_{iteration:06d}.pt")
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
            log(f"saved {path}", log_path, also_print)


if __name__ == "__main__":
    main()
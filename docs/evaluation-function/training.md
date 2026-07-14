# Training

[← Back to EvaluationFunction](../../EvaluationFunction/README.md)

## Overview

The training pipeline learns a neural-network-based evaluation function for Logix through repeated self-play.

The implementation follows an AlphaZero-inspired approach:

```text
Current network
      │
      ▼
Monte Carlo Tree Search
      │
      ▼
Self-play games
      │
      ▼
Training examples
      │
      ▼
Replay buffer
      │
      ▼
Network optimization
      │
      ▼
Updated checkpoint
```

The current neural network guides Monte Carlo Tree Search. MCTS produces improved move distributions, which are then used as training targets for the next network update.

The main training entry point is:

```text
EvaluationFunction/train.py
```

---

## Starting Training

From the `EvaluationFunction` directory, run:

```bash
python train.py
```

On systems where the provided shell script is supported, training may also be started using:

```bash
bash run_train.sh
```

The exact training parameters are defined in `train.py`.

These may include:

- number of self-play games,
- number of MCTS simulations,
- replay-buffer capacity,
- batch size,
- number of optimization steps,
- learning rate,
- checkpoint interval,
- maximum game length,
- temperature settings,
- device selection.

---

## Training Stages

Each training iteration consists of three main stages:

1. Self-play generation
2. Replay-buffer storage
3. Neural-network optimization

A checkpoint is saved periodically during this process.

---

## Self-Play Generation

Self-play games are generated using the current neural network and Monte Carlo Tree Search.

For every move:

1. The current game state is encoded.
2. MCTS is run for a configured number of simulations.
3. Root visit counts are converted into a move distribution.
4. A move is sampled or selected.
5. The environment advances to the next state.
6. The state and policy target are temporarily stored.

After the game ends, the final result is assigned to all stored positions.

A self-play training example contains:

```text
board tensor
feature vector
MCTS policy target
value target
```

The corresponding shapes are:

```text
board tensor:   (6, 7, 7)
feature vector: (99,)
policy target:  (2891,)
value target:   scalar
```

---

## Policy Target

The policy target is derived from MCTS root visit counts.

For each legal action:

```text
policy_target[action] =
    visit_count[action] / total_root_visits
```

Actions that were illegal in the current position remain zero.

The resulting vector has length:

```text
2891
```

This target is stronger than the raw network policy because it incorporates the additional search performed by MCTS.

---

## Value Target

The value target is derived from the final result of the self-play game.

Typical game results are:

```text
+1  first player wins
 0  draw
-1  second player wins
```

For training, the result must be converted to the perspective of the player associated with each stored state.

Conceptually:

```text
value_target =
    final_result × player_at_state
```

This means:

- a position belonging to the eventual winner receives a positive target,
- a position belonging to the eventual loser receives a negative target,
- positions from drawn games receive zero.

The exact sign convention must remain consistent between:

- self-play,
- replay-buffer storage,
- network training,
- inference,
- MCTS backup.

---

## Replay Buffer

Generated training examples are stored in the replay buffer.

The replay buffer allows the network to train on positions from multiple recent games instead of only the most recently generated game.

Its responsibilities include:

- storing self-play samples,
- limiting the maximum number of stored examples,
- sampling random mini-batches,
- mixing positions from different training iterations.

A replay-buffer sample conceptually contains:

```python
(
    board_tensor,
    feature_vector,
    policy_target,
    value_target,
)
```

Random sampling reduces correlation between consecutive game positions.

---

## Human Games

Recorded human games may optionally be loaded using:

```text
logix_az/human_loader.py
```

Human-game files are stored in:

```text
EvaluationFunction/recorded_games/
```

These games can be converted into training examples and added to the replay buffer.

Human data may be useful for:

- initializing training,
- exposing the model to meaningful positions,
- comparing self-play and human behaviour,
- supplementing limited self-play data.

Human-game loading is optional and depends on the current training configuration.

---

## Neural-Network Inputs

The network receives two inputs.

### Board Input

```text
(batch_size, 6, 7, 7)
```

The six board planes represent:

1. red marbles,
2. green marbles,
3. blue marbles,
4. yellow marbles,
5. grey marbles,
6. the black marble.

### Feature Input

```text
(batch_size, 99)
```

The feature vector contains additional state information such as:

- active player,
- inventory,
- forbidden colours,
- objective cards,
- turn-related features.

Both inputs must use the same encoding during training and inference.

---

## Neural-Network Outputs

The network produces two outputs.

### Policy Output

```text
(batch_size, 2891)
```

The policy head returns one logit for every encoded action.

These logits are trained to approximate the MCTS policy target.

### Value Output

```text
(batch_size, 1)
```

or an equivalent one-dimensional batch representation.

The value head estimates the expected game result from the active player's perspective.

---

## Loss Function

The total training loss combines policy loss and value loss.

Conceptually:

```text
total loss = policy loss + value loss
```

The policy loss compares the predicted policy distribution with the MCTS target.

A common formulation is cross-entropy:

```text
L_policy = -Σ π(a) log p(a)
```

where:

- `π(a)` is the MCTS target probability,
- `p(a)` is the predicted probability.

The value loss compares the predicted value with the final game result.

A common formulation is mean squared error:

```text
L_value = (z - v)²
```

where:

- `z` is the value target,
- `v` is the network prediction.

The complete loss may also include regularization depending on the implementation.

---

## Optimization

Training uses PyTorch optimization.

For each mini-batch:

1. Board and feature tensors are moved to the selected device.
2. The network performs a forward pass.
3. Policy and value losses are computed.
4. Gradients are cleared.
5. Backpropagation is performed.
6. Network parameters are updated.
7. Loss values may be written to the training log.

Conceptually:

```python
optimizer.zero_grad()

policy_logits, values = network(board_batch, feature_batch)

policy_loss = ...
value_loss = ...
loss = policy_loss + value_loss

loss.backward()
optimizer.step()
```

The exact optimizer and learning-rate settings are defined in `train.py`.

---

## Device Selection

Training can run on either:

- CPU,
- CUDA-compatible GPU.

A typical device selection is:

```python
device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)
```

GPU training is generally faster, especially for larger batch sizes.

The selected device must also be used when:

- loading checkpoints,
- running inference,
- generating self-play evaluations,
- exporting the network when required.

---

## Training Loop

A simplified training loop looks like:

```python
for iteration in range(number_of_iterations):

    generate_self_play_games()

    add_examples_to_replay_buffer()

    for step in range(training_steps):
        batch = replay_buffer.sample(batch_size)
        train_network(batch)

    save_checkpoint()
```

The real implementation may include:

- automatic resume,
- progress logging,
- human-game loading,
- buffer persistence,
- validation,
- checkpoint numbering,
- configurable self-play frequency.

---

## Temperature During Self-Play

Temperature controls how strongly MCTS visit counts determine move selection.

A common transformation is:

```text
P(a) ∝ N(a)^(1 / τ)
```

where:

- `N(a)` is the MCTS visit count,
- `τ` is the temperature.

Higher temperature produces more exploration.

Lower temperature favours the most visited action.

The implementation may use a non-zero temperature during early turns and choose the most visited action later in the game.

This produces varied self-play games while preserving stronger endgame play.

---

## Checkpoints

Model checkpoints are stored in:

```text
EvaluationFunction/checkpoints/
```

Checkpoint names use the format:

```text
net_000000.pt
net_000050.pt
net_000100.pt
...
```

The numeric part identifies the training stage or iteration.

Checkpoints allow:

- training to be resumed,
- models from different stages to be compared,
- selected models to be used in experiments,
- models to be exported to ONNX.

---

## Saving Checkpoints

A checkpoint should contain enough information to restore training.

Depending on the implementation, this may include:

- network parameters,
- optimizer state,
- training iteration,
- replay-buffer state,
- configuration,
- random-number generator state.

At minimum, the network state dictionary must be saved.

Conceptually:

```python
torch.save(
    {
        "iteration": iteration,
        "model_state_dict": network.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
    },
    checkpoint_path,
)
```

The exact saved structure should match the checkpoint-loading code.

---

## Resuming Training

Training should resume from the latest compatible checkpoint when requested.

The resume process typically performs:

1. Locate the selected checkpoint.
2. Recreate the same network architecture.
3. Load the model state.
4. Restore the optimizer state when available.
5. Restore the training iteration.
6. Continue checkpoint numbering.
7. Continue training using the loaded model.

A checkpoint can only be loaded safely when the following remain compatible:

- board-channel count,
- feature-vector size,
- action-space size,
- network architecture,
- state encoding,
- action encoding.

Changing any of these may require starting a new training run.

---

## Training Log

Training progress may be written to:

```text
EvaluationFunction/training_log.txt
```

Useful logged information includes:

- iteration number,
- number of generated games,
- replay-buffer size,
- policy loss,
- value loss,
- total loss,
- self-play duration,
- training duration,
- checkpoint path,
- device information.

Logs make it easier to detect:

- unstable loss,
- stalled training,
- unexpectedly slow self-play,
- invalid values,
- failed checkpoint saving.

---

## Numerical Stability

Training code should handle invalid numerical values carefully.

Potential issues include:

- non-finite policy logits,
- invalid softmax values,
- exploding gradients,
- empty legal-action masks,
- NaN losses,
- corrupted replay-buffer samples.

The MCTS implementation may fall back to a uniform distribution over legal moves when policy logits are invalid.

Training should still report such cases because repeated fallbacks may indicate a problem in the network or training data.

---

## Reproducibility

Training behaviour may depend on:

- Python random seeds,
- NumPy random seeds,
- PyTorch random seeds,
- CUDA behaviour,
- objective-card assignment,
- self-play sampling,
- replay-buffer sampling.

A reproducible setup should initialize all relevant random-number generators.

Conceptually:

```python
import random
import numpy as np
import torch

random.seed(seed)
np.random.seed(seed)
torch.manual_seed(seed)

if torch.cuda.is_available():
    torch.cuda.manual_seed_all(seed)
```

Complete GPU determinism may reduce performance and is not guaranteed for every operation.

---

## Monitoring Training Quality

Loss alone does not fully measure agent strength.

Useful evaluation methods include:

- comparing checkpoints in head-to-head matches,
- measuring win rate against fixed baseline agents,
- testing against `RandomBot`,
- testing against `HeuristicBot`,
- comparing older and newer checkpoints,
- observing average game length,
- inspecting policy distributions,
- manually playing against selected models.

The `BotExperiments` module is used for this purpose.

A newer checkpoint should not automatically be assumed to be stronger without evaluation.

---

## Common Training Problems

### Replay Buffer Too Small

A small replay buffer may cause the network to overfit recent games.

### Replay Buffer Too Large

A very large buffer may contain outdated samples produced by much weaker networks.

### Too Few MCTS Simulations

Weak search produces noisy policy targets.

### Too Many MCTS Simulations

Training becomes slow because self-play dominates execution time.

### Incorrect Value Perspective

A sign error in value-target generation can prevent meaningful learning.

### Illegal Policy Entries

Failure to mask illegal actions can assign probability to impossible moves.

### Incompatible Checkpoints

Changing network dimensions or encodings makes previous checkpoints incompatible.

### Low Self-Play Diversity

Always selecting the most visited action may produce repetitive games.

### Unstable Optimization

An excessive learning rate or invalid targets may produce NaN values.

---

## Performance Considerations

The most computationally expensive stage is usually self-play.

Each move may require many MCTS simulations, and every simulation can involve:

- state copying,
- legal-move generation,
- neural-network inference,
- tree traversal,
- backpropagation.

Possible optimizations include:

- batched neural-network inference,
- faster state copying,
- caching encoded states,
- caching network evaluations,
- reducing unnecessary legal-move generation,
- parallel self-play workers,
- GPU inference,
- more efficient MCTS data structures.

Optimization should preserve rule correctness and state independence.

---

## Exporting a Trained Model

After selecting a checkpoint, export it using:

```bash
python export_onnx.py
```

The exported model is stored in:

```text
EvaluationFunction/onnx/
```

The ONNX model preserves the network interface:

```text
board input:    (batch, 6, 7, 7)
feature input:  (batch, 99)
policy output:  (batch, 2891)
value output:   (batch, 1)
```

The exported model can then be integrated into the Unity application.

---

## Recommended Training Workflow

A practical workflow is:

1. Verify environment tests.
2. Verify state and action encoding.
3. Run a short self-play test.
4. Train for a small number of iterations.
5. Confirm that checkpoints are created.
6. Confirm that losses are finite.
7. Run a small tournament against baseline bots.
8. Resume training from a checkpoint.
9. Compare later checkpoints.
10. Export the selected model to ONNX.
11. Validate Python and Unity inference on the same state.

---

## Files Involved

| File | Responsibility |
|---|---|
| `train.py` | Main training coordinator |
| `run_train.sh` | Optional shell-based training launcher |
| `logix_az/selfplay.py` | Self-play game generation |
| `logix_az/mcts.py` | Search used during self-play |
| `logix_az/net.py` | Neural-network architecture |
| `logix_az/replay_buffer.py` | Training-data storage |
| `logix_az/state_encoding.py` | Network input creation |
| `logix_az/action_encoding.py` | Policy index mapping |
| `logix_az/human_loader.py` | Recorded human-game loading |
| `checkpoints/` | Saved PyTorch models |
| `training_log.txt` | Training progress log |
| `export_onnx.py` | ONNX export entry point |

---

## Compatibility Requirements

A complete training run assumes fixed definitions for:

```text
board shape
board-plane order
feature-vector length
feature-vector order
action-space size
action offsets
network architecture
value perspective
checkpoint structure
```

Changing one of these interfaces requires coordinated changes throughout the framework and will usually invalidate existing checkpoints.

---

## Related Documentation

- [Evaluation Function Overview](overview.md)
- [Game Environment](environment.md)
- [State and Action Encoding](state-and-action-encoding.md)
- [Neural Network](neural-network.md)
- [MCTS and Self-Play](mcts-and-self-play.md)
- [Bot Experiments](../bot-experiments/overview.md)
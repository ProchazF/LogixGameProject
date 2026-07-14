# Neural Network

[← Back to EvaluationFunction](../../EvaluationFunction/README.md)

## Overview

The neural network provides the learned evaluation function used throughout the project.

Instead of relying solely on handcrafted heuristics or random simulations, the network estimates:

- the probability of selecting each possible action (**policy**),
- the expected outcome of the current position (**value**).

The implementation follows the general design introduced by AlphaZero, where a single network jointly predicts both outputs.

The network is implemented in:

```text
logix_az/net.py
```

and is used by:

- Monte Carlo Tree Search,
- self-play generation,
- model inference,
- ONNX export,
- experimental agents.

---

## Network Inputs

The network receives two independent inputs.

### Board Tensor

The first input is the encoded board.

Shape:

```text
(batch_size, 6, 7, 7)
```

The six feature planes represent:

| Plane | Content |
|---:|---|
| 0 | Red marbles |
| 1 | Green marbles |
| 2 | Blue marbles |
| 3 | Yellow marbles |
| 4 | Grey marbles |
| 5 | Black marble |

This tensor is processed using convolutional layers.

---

### Feature Vector

The second input is a non-spatial feature vector.

Shape:

```text
(batch_size, 99)
```

The feature vector contains information that cannot be represented directly on the board, including:

- current player,
- remaining inventory,
- forbidden colours,
- objective cards,
- additional game-state features.

The board tensor and feature vector are processed separately before being combined later in the network.

---

## Network Architecture

The network consists of three logical parts.

```text
             Board Tensor
                   │
                   ▼
        Convolutional Backbone
                   │
                   ▼
        Spatial Feature Vector
                   │
                   ├──────────────┐
                   │              │
Feature Vector ────┘              │
                                  ▼
                        Combined Features
                                  │
                     ┌────────────┴────────────┐
                     ▼                         ▼
                Policy Head              Value Head
```

The convolutional backbone extracts spatial information from the board, while the additional feature vector provides global game-state information.

The resulting representations are concatenated and passed to two independent output heads.

---

## Convolutional Backbone

The convolutional part of the network is responsible for learning spatial patterns such as:

- local marble configurations,
- objective shapes,
- blocking structures,
- board connectivity,
- tactical opportunities.

Unlike handcrafted heuristics, these features are learned directly from self-play data.

The output of the convolutional layers is flattened into a one-dimensional representation before being combined with the additional feature vector.

---

## Feature Fusion

After processing the board tensor, the resulting spatial representation is concatenated with the 99-dimensional feature vector.

Conceptually:

```text
board features
        │
        ▼
flatten
        │
        ▼
concatenate
        ▲
        │
additional features
```

This allows the network to consider both:

- spatial information,
- global game information,

when predicting the policy and value.

---

## Policy Head

The policy head predicts one value for every encoded action.

Output shape:

```text
(batch_size, 2891)
```

Each output corresponds to one action index produced by `action_encoding.py`.

The output represents raw policy logits.

Illegal actions are **not** removed by the network itself.

Instead, a legal-action mask is applied later by the search algorithm.

The policy head therefore always predicts the complete fixed action space.

---

## Value Head

The value head predicts the expected outcome of the current position.

Output shape:

```text
(batch_size, 1)
```

The value is interpreted from the perspective of the active player.

Typical values are:

| Value | Interpretation |
|---:|---|
| `+1` | Winning position |
| `0` | Approximately equal position |
| `-1` | Losing position |

Intermediate values represent the network's confidence about the expected outcome.

---

## Forward Pass

A simplified forward pass is:

```text
Board Tensor
      │
      ▼
Convolutional Layers
      │
      ▼
Flatten
      │
      ├───────────────┐
      │               │
Feature Vector ───────┘
      │
      ▼
Fully Connected Layers
      │
      ├──────────────┐
      ▼              ▼
Policy Head     Value Head
```

The network returns both outputs simultaneously.

Conceptually:

```python
policy_logits, value = network(
    board_tensor,
    feature_vector,
)
```

---

## Training Targets

The network is trained using two targets.

### Policy Target

The policy target comes from Monte Carlo Tree Search.

Rather than learning directly from played moves, the network learns to imitate the improved move distribution produced by MCTS.

The target has shape:

```text
(batch_size, 2891)
```

---

### Value Target

The value target is the final game result.

Typical values are:

```text
+1
0
-1
```

converted to the perspective of the player associated with each stored state.

---

## Loss Function

Training minimizes two objectives simultaneously.

### Policy Loss

The policy head learns to approximate the MCTS policy distribution.

Conceptually:

```text
Lpolicy = -Σ π(a) log p(a)
```

where:

- `π(a)` is the MCTS target,
- `p(a)` is the predicted probability.

---

### Value Loss

The value head predicts the expected game outcome.

Conceptually:

```text
Lvalue = (z - v)²
```

where:

- `z` is the target value,
- `v` is the predicted value.

---

### Total Loss

The complete optimization objective is:

```text
L = Lpolicy + Lvalue
```

Additional regularization may be included depending on the implementation.

---

## Inference

During inference:

1. The current game state is encoded.
2. The network predicts policy logits and a value.
3. Illegal actions are masked.
4. The policy guides Monte Carlo Tree Search.
5. The value evaluates newly expanded nodes.

The network is therefore used as an evaluation function rather than selecting moves directly.

---

## Checkpoints

Trained models are stored as PyTorch checkpoints.

Typical location:

```text
EvaluationFunction/checkpoints/
```

Example:

```text
net_010000.pt
```

A checkpoint stores the learned network parameters and, depending on the training configuration, may also contain optimizer state and additional metadata.

Checkpoints are used for:

- resuming training,
- model evaluation,
- tournament experiments,
- ONNX export.

---

## ONNX Export

Once training is complete, a checkpoint can be exported using:

```bash
python export_onnx.py
```

The exported model preserves the same interface:

Inputs:

```text
board:    (batch, 6, 7, 7)
features: (batch, 99)
```

Outputs:

```text
policy: (batch, 2891)
value:  (batch, 1)
```

The ONNX model can then be loaded by the Unity application.

---

## Compatibility Requirements

The following properties define the network interface and must remain consistent across the project:

- board tensor shape,
- board-plane ordering,
- feature-vector length,
- feature ordering,
- action-space size,
- policy-output ordering,
- value interpretation.

Changing any of these requires corresponding changes to:

- state encoding,
- action encoding,
- MCTS,
- training,
- checkpoint loading,
- ONNX export,
- Unity inference.

Existing checkpoints are generally incompatible with such changes.

---

## Common Failure Modes

Typical implementation errors include:

- incorrect feature ordering,
- inconsistent action indexing,
- mismatched tensor dimensions,
- incorrect player perspective,
- incompatible checkpoints,
- stale ONNX models,
- missing legal-action masking.

Most of these errors do not produce runtime exceptions but instead lead to poor playing strength, making careful validation particularly important.

---

## Related Documentation

- [Evaluation Function Overview](overview.md)
- [Game Environment](environment.md)
- [State and Action Encoding](state-and-action-encoding.md)
- [MCTS and Self-Play](mcts-and-self-play.md)
- [Training](training.md)
# Evaluation Function Overview

[← Back to EvaluationFunction](../../EvaluationFunction/README.md)

## Purpose

The **EvaluationFunction** module provides a complete Python framework for developing, training, and evaluating neural-network-based evaluation functions for the board game **Logix**.

Unlike the Unity implementation, which focuses on gameplay and user interaction, this module serves as an experimental environment for artificial intelligence research. It reproduces the complete game rules independently of the game engine and provides all components required for reinforcement learning, including state representation, Monte Carlo Tree Search (MCTS), self-play generation, neural-network training, and model export.

The trained evaluation networks can be exported to the ONNX format and integrated directly into the Unity application, allowing the game to use models trained entirely within the Python framework.

---

# Framework Architecture

The framework consists of several independent modules, each responsible for one stage of the training pipeline.

```text
                Logix Game Environment
                         │
                         ▼
            State & Action Encoding
                         │
                         ▼
        Monte Carlo Tree Search (MCTS)
                         │
                         ▼
               Self-Play Generation
                         │
                         ▼
                  Replay Buffer
                         │
                         ▼
              Neural Network Training
                         │
                         ▼
                  Model Checkpoints
                         │
                         ▼
                   ONNX Model Export
```

Each module communicates only through well-defined interfaces, making the framework modular and easy to extend.

---

# Project Structure

The main implementation resides in the `logix_az` package.

| Module | Responsibility |
|---------|----------------|
| `env_logix.py` | Base implementation of the Logix game environment. |
| `env_logix_helper.py` | Complete environment used for training, inference, and experiments. |
| `state_encoding.py` | Converts symbolic game states into tensors used by the neural network. |
| `action_encoding.py` | Maps legal moves to unique policy-output indices. |
| `net.py` | Defines the PyTorch evaluation network. |
| `mcts.py` | Implements neural-network-guided Monte Carlo Tree Search. |
| `selfplay.py` | Generates self-play games using the current network. |
| `replay_buffer.py` | Stores and samples generated training examples. |
| `human_loader.py` | Loads recorded human games when available. |
| `infer.py` | Performs inference using trained checkpoints. |
| `export.py` | Utilities used during model export. |
| `train.py` | Coordinates the complete training process. |
| `export_onnx.py` | Converts trained checkpoints into ONNX models. |

---

# Training Workflow

Training follows an iterative AlphaZero-inspired reinforcement learning process.

Each iteration consists of four stages:

1. Generate self-play games using the current neural network.
2. Store generated training samples inside the replay buffer.
3. Train the neural network using randomly sampled mini-batches.
4. Save the updated model and repeat the process.

The neural network gradually improves through repeated interaction with increasingly stronger versions of itself.

---

# Data Flow

Each self-play game generates a sequence of training examples.

Every example contains:

```text
(
    encoded_state,
    MCTS_policy,
    game_result
)
```

where

- **encoded_state** is the neural-network input,
- **MCTS_policy** is obtained from the visit counts at the root node,
- **game_result** is the final outcome of the game from the current player's perspective.

These samples are stored in the replay buffer and later used to optimize the policy and value heads of the network.

---

# Neural Network

The framework uses a neural network that predicts two quantities simultaneously:

- **Policy** – a probability distribution over the complete action space.
- **Value** – an estimate of the expected game outcome.

The current implementation operates on

- a **6 × 7 × 7** board tensor,
- an additional **99-dimensional** feature vector.

The policy head predicts probabilities over a fixed action space containing **2891** possible actions.

---

# Monte Carlo Tree Search

The framework uses Monte Carlo Tree Search to improve move selection during both training and inference.

Instead of relying on random simulations, newly expanded nodes are evaluated directly by the neural network.

Each search iteration performs:

1. Selection
2. Expansion
3. Neural-network evaluation
4. Backpropagation

The resulting visit counts are used both to select moves during self-play and to generate policy targets for neural-network training.

---

# Model Export

Once training is complete, the network can be exported to the ONNX format.

This enables the same evaluation network to be used inside the Unity implementation without requiring a Python runtime.

The export pipeline is:

```text
PyTorch Checkpoint
        │
        ▼
 export_onnx.py
        │
        ▼
     ONNX Model
        │
        ▼
 Unity Barracuda Runtime
```

---

# Design Principles

Several design decisions guided the implementation of the framework.

- **Modularity** — game logic, search, encoding, and neural-network implementation are separated into independent modules.
- **Reproducibility** — experiments can be repeated using saved checkpoints and recorded configurations.
- **Extensibility** — alternative search algorithms or neural-network architectures can be integrated with minimal changes.
- **Platform Independence** — training is performed entirely in Python, while deployment is supported through ONNX export.
- **Consistency** — the Python environment reproduces the same rules as the Unity implementation to ensure compatibility between training and gameplay.

---

# Related Documentation

The following documents describe the individual components of the framework in greater detail:

- **Environment** – implementation of the Logix game environment.
- **State and Action Encoding** – numerical representation used by the neural network.
- **Neural Network** – architecture and inference pipeline.
- **MCTS and Self-Play** – search algorithm and training data generation.
- **Training** – complete reinforcement learning workflow and configuration.
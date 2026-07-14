# Evaluation Function for Logix

---

## Overview

This project provides a Python framework for training, evaluating, and deploying neural network-based evaluation functions for the board game **Logix**.

The framework implements an AlphaZero-inspired reinforcement learning pipeline that combines self-play, Monte Carlo Tree Search (MCTS), and deep neural networks to learn position evaluation directly from gameplay. Instead of relying solely on handcrafted heuristics, the neural network is trained to estimate the quality of game positions and guide the search process during decision making.

The project includes a complete implementation of the Logix game environment, training infrastructure, replay buffer management, neural network architecture, model checkpointing, and utilities for testing, visualization, and recording human games. Trained models can be exported to the ONNX format and integrated into the Unity implementation of the game.

This framework was developed as part of a bachelor's thesis focused on designing AI agents for Logix and investigating the use of neural network evaluation functions in search-based game-playing algorithms.

## Features

- Complete Python implementation of the **Logix** game environment
- AlphaZero-inspired reinforcement learning pipeline
- Monte Carlo Tree Search (MCTS) guided by a neural network
- Self-play data generation and replay buffer management
- PyTorch implementation of the evaluation network
- Training checkpoint management
- ONNX model export for Unity integration
- Utilities for visualization, debugging, and human game recording

## Project Structure

```
EvaluationFunction/
│
├── train.py                  # Main training script
├── export_onnx.py            # Export trained models to ONNX
├── requirements.txt          # Python dependencies
├── run_train.sh              # Example training script
│
├── logix_az/                 # Core implementation
│   ├── env_logix.py          # Game environment
│   ├── env_logix_helper.py   # Helper environment for experiments
│   ├── action_encoding.py    # Action encoding and decoding
│   ├── state_encoding.py     # Neural network input representation
│   ├── net.py                # Neural network architecture
│   ├── mcts.py               # Monte Carlo Tree Search
│   ├── selfplay.py           # Self-play generation
│   ├── replay_buffer.py      # Experience replay buffer
│   ├── infer.py              # Model inference
│   └── export.py             # Export utilities
│
├── checkpoints/              # Saved training checkpoints
├── onnx/                     # Exported ONNX models
├── scripts/                  # Utility and debugging scripts
├── recorded_games/           # Human game recordings
├── position_examples/        # Example board positions
└── README.md
```

### Main Components

| Component | Description |
|-----------|-------------|
| `train.py` | Entry point for training the evaluation network. |
| `logix_az/` | Contains the core implementation of the game environment, neural network, MCTS, self-play, and training utilities. |
| `checkpoints/` | Stores periodically saved network checkpoints during training. |
| `onnx/` | Contains exported ONNX models used by the Unity implementation. |
| `scripts/` | Helper scripts for testing, visualization, debugging, and recording games. |
| `recorded_games/` | Human-played games that can be used for analysis or future training. |
| `position_examples/` | Example board positions generated during development and debugging. |

## Installation

### Prerequisites

Before installing the project, ensure that the following software is available:

- Python 3.12 or newer
- pip package manager
- Git (optional, for cloning the repository)

### Clone the Repository

```bash
git clone https://gitlab.mff.cuni.cz/teaching/nprg045/majerech/frantisek-prochazka.git
cd <repository>/EvaluationFunction
```

### Install Dependencies

Install the required Python packages using

```bash
pip install -r requirements.txt
```

The framework has been developed and tested on Windows, but it is platform-independent and should also run on Linux and macOS provided that the required dependencies are installed.

## Quick Start

Train a new evaluation network:

```bash
python train.py
```

Export the trained model for use in the Unity project:

```bash
python export_onnx.py
```

Launch the graphical interface for testing positions:

```bash
python play_gui.py
```

## Training

The evaluation network is trained through repeated self-play games. During self-play, the current neural network guides Monte Carlo Tree Search, which selects moves and produces improved policy targets from its visit counts.

Each generated game provides training examples consisting of:

- an encoded game state,
- a target policy derived from MCTS visit counts,
- the final game result used as the value target.

These examples are stored in a replay buffer and sampled in mini-batches during training. The network is optimized jointly for policy prediction and position evaluation.

Training can be started with:

```bash
python train.py
```

The training configuration, including the number of self-play games, MCTS simulations, batch size, learning rate, and checkpoint frequency, is defined in `train.py`.

Model checkpoints are saved periodically in the `checkpoints/` directory. These checkpoints allow training to be resumed and make it possible to compare models from different stages of the training process.

On Linux-based systems, training can also be started using:

```bash
bash run_train.sh
```

## Training Pipeline

The training process follows an AlphaZero-inspired iterative pipeline:

1. The current neural network is loaded.
2. Self-play games are generated using MCTS.
3. MCTS visit counts are converted into policy targets.
4. Final game outcomes are assigned as value targets.
5. Training samples are stored in the replay buffer.
6. Mini-batches are sampled from the replay buffer.
7. The neural network is updated using policy and value losses.
8. A new checkpoint is saved.
9.  The updated network is used in the next self-play iteration.

```text
Current Network
      │
      ▼
Monte Carlo Tree Search
      │
      ▼
Self-Play Games
      │
      ▼
Training Examples
(state, policy, result)
      │
      ▼
Replay Buffer
      │
      ▼
Neural Network Training
      │
      ▼
Updated Network
      │
      └───────────────► Next Iteration
```

The policy head is trained to approximate the move distribution produced by MCTS, while the value head is trained to predict the final outcome of the game from the current player's perspective.

This creates a feedback loop in which the neural network improves the search, while the improved search produces stronger training targets for the neural network.

## Evaluation Neural Network

The evaluation network is implemented in **PyTorch** and serves as the core component guiding the search algorithm. Instead of relying on handcrafted evaluation heuristics, the network learns to estimate the quality of game positions directly from self-play experience.

The network receives an encoded representation of the current game state and produces two outputs:

- **Policy** – a probability distribution over all possible actions, indicating promising moves.
- **Value** – an estimate of the expected game outcome from the perspective of the current player.

During training, both outputs are optimized simultaneously. The policy head learns to approximate the move distribution generated by Monte Carlo Tree Search, while the value head learns to predict the final game result.

The trained network is used both during self-play to guide the search process and during inference to evaluate previously unseen game positions.

## Monte Carlo Tree Search

Move selection is performed using **Monte Carlo Tree Search (MCTS)** guided by the neural network. Rather than exploring the game tree uniformly, the search uses the network's policy predictions to prioritize promising actions and its value estimates to evaluate newly expanded positions.

Each search iteration consists of four phases:

1. **Selection** – traverse the search tree according to the UCT selection rule.
2. **Expansion** – create a new node when an unexplored position is reached.
3. **Evaluation** – use the neural network to obtain policy and value predictions for the new position.
4. **Backpropagation** – propagate the evaluation back through the visited nodes, updating search statistics.

After a predefined number of simulations, the visit counts of the root node are used to determine the move played during self-play. These visit counts also serve as policy targets for neural network training.

By combining statistical search with learned position evaluation, MCTS is able to explore significantly stronger moves than either approach could achieve independently.

## Game Representation

The Logix game is implemented as a custom environment that fully reproduces the game rules used by the Unity application. This ensures that the neural network is trained under the same conditions in which it is later deployed.

Each game state is converted into a fixed-size numerical representation suitable for neural network processing. The encoded state includes information about:

- the current board configuration,
- the positions and colours of all pieces,
- the current player,
- remaining piece inventory,
- currently forbidden colours,
- player objectives,
- additional game-specific information required to reconstruct the complete state.

Similarly, every legal action is mapped to a unique integer identifier, allowing the policy network to predict probabilities over the entire action space while masking illegal moves during search.

The state and action encoding modules provide the interface between the game environment, the neural network, and the Monte Carlo Tree Search implementation.

## Exporting the Model

After training, the evaluation network can be exported to the **ONNX (Open Neural Network Exchange)** format for deployment in external applications.

Exporting the model is performed using:

```bash
python export_onnx.py
```

The generated ONNX model is stored in the `onnx/` directory and can be loaded by the Unity implementation of Logix using the Barracuda inference library.

Using the ONNX format decouples the training framework from the game engine, allowing the model to be trained in Python while being evaluated efficiently inside the Unity application without requiring a Python runtime.

## Utility Scripts

In addition to the core training framework, the project includes several utility scripts that simplify development, debugging, and testing.

| Script | Description |
|---------|-------------|
| `play_gui.py` | Launches a graphical interface for testing and visualizing game positions. |
| `play_against_bot.py` | Allows a human player to play against the trained evaluation network. |
| `record_human_game.py` | Records human-played games for future analysis or training. |
| `print_positions.py` | Generates visual representations of selected board positions. |
| `print_shapes.py` | Visualizes the objective shapes used in the game. |
| `testing.py` | Contains helper routines for validating the implementation during development. |

These scripts are intended primarily for development and experimentation and are not required for the standard training pipeline.

## Documentation

Detailed technical documentation is available in the repository-level [`docs/evaluation-function/`](../docs/evaluation-function/) directory.

- [Evaluation Function Overview](../docs/evaluation-function/overview.md)  
  High-level architecture, training workflow, major modules, and data flow.

- [Game Environment](../docs/evaluation-function/environment.md)  
  Environment state, legal actions, inventory management, move execution, simulation, and termination.

- [State and Action Encoding](../docs/evaluation-function/state-and-action-encoding.md)  
  Board planes, feature-vector representation, action indexing, legal-action masking, and neural-network interfaces.

- [Neural Network](../docs/evaluation-function/neural-network.md)  
  Network inputs, policy and value outputs, inference, checkpoints, and ONNX compatibility.

- [MCTS and Self-Play](../docs/evaluation-function/mcts-and-self-play.md)  
  Tree search, node statistics, policy targets, value backup, move selection, and self-play data generation.

- [Training](../docs/evaluation-function/training.md)  
  Replay-buffer usage, optimization, losses, checkpoint management, resuming training, and model export.

The complete game rules shared by the Python and Unity implementations are documented separately in the [Logix Game Rules](../docs/game-rules.md).

## Related Components

This framework is one component of a larger project developed as part of a bachelor's thesis. The complete project consists of:

- **LogixGame** – a Unity implementation of the Logix board game supporting human and AI players.
- **EvaluationFunction** *(this project)* – a Python framework for training and exporting neural network evaluation functions.
- **BotExperiments** – a collection of scripts used to evaluate and compare different game-playing agents through automated tournaments.
- **BachelorsThesis** – the written thesis describing the design, implementation, and experimental evaluation of the project.

Together, these components provide a complete pipeline covering game implementation, AI development, experimental evaluation, and documentation.

## Future Work

Several directions remain open for future development:

- Improve the neural network architecture and investigate deeper or residual models.
- Optimize the Monte Carlo Tree Search implementation for faster search.
- Extend self-play with distributed game generation.
- Investigate alternative reinforcement learning strategies and hyperparameter optimization.
- Evaluate the framework on larger datasets and longer training runs.

The modular structure of the project allows individual components, such as the game environment, search algorithm, or neural network, to be replaced or extended independently.
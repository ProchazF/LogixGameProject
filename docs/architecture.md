# Project Architecture

[← Back to main repository](../README.md)

## Overview

The Logix project is divided into several components that cover game implementation, neural-network training, artificial intelligence agents, and experimental evaluation.

The main components are:

- **LogixGame** – Unity implementation of the game.
- **EvaluationFunction** – Python framework for self-play training and neural-network evaluation.
- **BotExperiments** – framework for comparing implemented agents through automated tournaments.
- **BachelorsThesis** – LaTeX source of the accompanying bachelor's thesis.
- **Builds** – compiled versions of the Unity application.

Each component is developed independently but shares the same game rules and state representation.

## Repository Structure

```text
.
├── LogixGame/              # Unity game implementation
├── EvaluationFunction/     # Neural-network training framework
├── BotExperiments/         # Agent evaluation and tournaments
├── BachelorsThesis/        # Bachelor's thesis source
├── Builds/                 # Compiled game builds
├── docs/                   # Technical documentation
└── README.md
```

## High-Level Data Flow

```text
                     ┌──────────────────────┐
                     │      LogixGame       │
                     │                      │
                     │ Unity application    │
                     │ Human and AI players │
                     └──────────┬───────────┘
                                │
                                │ ONNX model
                                │
                     ┌──────────▼───────────┐
                     │ EvaluationFunction   │
                     │                      │
                     │ Game environment     │
                     │ MCTS and self-play   │
                     │ Neural training      │
                     └──────────┬───────────┘
                                │
                                │ PyTorch checkpoints
                                │
                     ┌──────────▼───────────┐
                     │   BotExperiments     │
                     │                      │
                     │ Automated matches    │
                     │ Tournament results   │
                     │ Performance plots    │
                     └──────────────────────┘
```

The Python training framework produces neural-network checkpoints. Selected checkpoints can be used by experimental agents or exported to ONNX for integration into the Unity project.

## LogixGame

`LogixGame` contains the playable Unity implementation.

Its responsibilities include:

- displaying the game board,
- processing player input,
- managing turns,
- validating and executing moves,
- assigning objective cards,
- detecting winning positions,
- controlling game modes,
- running computer-controlled players,
- displaying menus and game status.

### Main Unity Layers

```text
Main Menu
    │
    ▼
Game Configuration
    │
    ▼
Game Manager
    │
    ├── Player controllers
    ├── Game board
    ├── Move validation
    ├── Objective cards
    ├── Win detection
    └── User interface
```

### Important Components

| Component | Responsibility |
|---|---|
| `MainMenuManager` | Handles menu navigation and game-mode selection. |
| `GameManager` | Controls match initialization, turns, players, and game completion. |
| `GameBoard` | Stores board state and applies game rules. |
| `Move` | Represents a placement, movement, or replacement action. |
| `WinShape` | Represents an objective shape and its transformations. |
| Player controllers | Request moves from either a human or an AI agent. |
| Bot controllers | Convert the current game state into an AI-selected move. |
| UI components | Display inventories, objective cards, player status, and board updates. |

## EvaluationFunction

`EvaluationFunction` contains the Python implementation used to train a learned evaluation function.

The training system follows an AlphaZero-inspired workflow:

```text
Game environment
      │
      ▼
State and action encoding
      │
      ▼
Monte Carlo Tree Search
      │
      ▼
Self-play games
      │
      ▼
Replay buffer
      │
      ▼
Neural-network training
      │
      ▼
Updated checkpoint
```

### Main Modules

| Module | Responsibility |
|---|---|
| `env_logix.py` | Defines the base game environment. |
| `env_logix_helper.py` | Provides the complete environment used by training and experiments. |
| `state_encoding.py` | Converts game states into neural-network inputs. |
| `action_encoding.py` | Converts moves to and from policy-output indices. |
| `net.py` | Defines the PyTorch policy and value network. |
| `mcts.py` | Implements neural-network-guided Monte Carlo Tree Search. |
| `selfplay.py` | Generates training games using the current network. |
| `replay_buffer.py` | Stores and samples generated training examples. |
| `human_loader.py` | Loads recorded human games when required. |
| `infer.py` | Provides neural-network inference utilities. |
| `export.py` | Provides model-export utilities. |
| `train.py` | Coordinates self-play, training, logging, and checkpoint saving. |
| `export_onnx.py` | Exports a trained checkpoint to ONNX. |

## Neural-Network Interface

The evaluation network receives an encoded game state and produces two outputs:

- **Policy output** – scores or probabilities for actions.
- **Value output** – estimated game outcome from the current player's perspective.

The policy output is used to prioritize actions during search. Illegal actions are masked before move selection.

The value output replaces random rollouts or handcrafted leaf evaluation in neural-network-guided search.

## State Representation

The encoded state includes the information necessary to describe a complete Logix position:

- board contents,
- black-marble position,
- current player,
- remaining inventory,
- forbidden colours,
- recently played colours,
- player objective cards,
- turn-related information.

Board contents are represented using separate feature planes for the individual marble colours.

Additional non-spatial information is represented using a feature vector.

## Action Representation

The action space contains three action categories:

1. **Placement**
2. **Movement**
3. **Replacement**

Each possible action has a unique integer index. This makes it possible for the policy network to produce a fixed-size output independently of the number of currently legal moves.

Before an action is selected, the environment generates the legal-action set and all illegal policy entries are masked.

## Monte Carlo Tree Search

The neural MCTS stores statistics for each action:

- prior probability,
- visit count,
- accumulated value,
- child node.

A search simulation performs:

1. selection,
2. expansion,
3. neural-network evaluation,
4. backpropagation.

After the required number of simulations, root visit counts are used to select the move and to create the policy target for training.

## Self-Play and Training

During self-play, MCTS is used to choose each move. Every visited position produces a training example containing:

```text
(encoded state, MCTS policy target, final game result)
```

The examples are stored in a replay buffer. The network is then trained using mini-batches sampled from the buffer.

Training optimizes two objectives:

- policy prediction,
- game-result prediction.

Checkpoints are saved periodically and may be used to resume training, compare different training stages, run experiments, or export the model.

## BotExperiments

`BotExperiments` evaluates different agents under comparable conditions.

The framework supports:

- repeated games,
- alternating player positions,
- configurable maximum game length,
- match resumption,
- result saving after completed matches,
- aggregated statistics,
- generated plots.

### Main Files

| File | Responsibility |
|---|---|
| `bots.py` | Contains implementations of evaluated agents. |
| `run_experiment.py` | Runs selected head-to-head experiments. |
| `play_tournament.py` | Runs complete tournaments between multiple agents. |
| `human_vs_bot.py` | Allows manual testing against an agent. |
| `concatenate_results.py` | Combines multiple result sets. |

### Evaluated Agent Types

The framework includes agents based on several approaches:

- random move selection,
- handcrafted heuristic evaluation,
- alpha-beta search,
- neural-network-assisted alpha-beta search,
- Monte Carlo Tree Search.

All bots expose a compatible move-selection interface so they can be exchanged without changing the match runner.

## Model Exchange

Two model formats are used by the project:

### PyTorch checkpoints

PyTorch checkpoint files are used by Python training and experimental agents.

```text
EvaluationFunction/checkpoints/
BotExperiments/EvalFunction/
```

### ONNX models

ONNX models are exported for deployment outside the Python training environment, particularly in the Unity application.

```text
EvaluationFunction/onnx/
```

The export process allows the model to be trained using PyTorch while being evaluated by a different runtime.

## Shared Game Rules

The Unity and Python implementations must follow the same game rules.

The following behaviour must remain consistent:

- board size,
- initial black-marble placement,
- inventory limits,
- legal placement rules,
- legal movement rules,
- replacement rules,
- colour restrictions,
- objective-card matching,
- use of grey marbles,
- exact-shape validation,
- game termination.

Any rule change should therefore be applied to both implementations.

See [Game Rules](game-rules.md) for the complete rule summary.

## Extension Points

The project was designed so individual components can be extended independently.

### Adding a new Python bot

A new bot should:

1. accept the current environment or game state,
2. generate or receive the legal moves,
3. return one legal move,
4. follow the interface used by the experiment scripts.

### Adding a new Unity bot

A new Unity bot should:

1. implement the expected bot or player interface,
2. receive the current board state,
3. select a legal move,
4. return control to the game manager,
5. avoid blocking the Unity main thread unnecessarily.

### Replacing the neural network

A replacement network must preserve the expected interface:

- compatible state input,
- fixed-size policy output,
- scalar value output.

If the input or action encoding changes, the training, inference, experimental, and export code must be updated together.

## Documentation Responsibilities

The documentation is divided into three levels:

- the root `README.md` introduces the complete repository,
- component README files explain installation and usage,
- files in `docs/` describe architecture, data formats, and implementation details.

Source-code comments and docstrings should document non-obvious class behaviour, public interfaces, assumptions, and edge cases.
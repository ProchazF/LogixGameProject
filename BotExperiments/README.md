# Bot Experiments

> Framework for evaluating and comparing Logix-playing agents through automated tournaments.

---

## Overview

This project provides a framework for evaluating and comparing different artificial intelligence agents developed for the board game **Logix**.

The framework automates large-scale tournaments between implemented agents, records detailed game statistics, and produces quantitative performance measures such as win rate, average game length, and head-to-head comparisons. It was primarily developed to evaluate the effectiveness of different search algorithms and neural network evaluation functions during the development of the project.

The modular architecture allows new agents to be integrated with minimal changes, making the framework suitable for benchmarking additional approaches in future work.

## Features

- Automated tournaments between multiple Logix-playing agents
- Support for heuristic, search-based, and neural-network-assisted agents
- Configurable tournament settings, including number of games and random seeds
- Automatic collection of detailed match statistics
- Generation of summary reports and visualizations
- Support for resuming interrupted tournaments
- Modular framework for benchmarking newly developed agents
  
## Project Structure

```
BotExperiments/
│
├── bots.py                     # Implemented game-playing agents
├── play_tournament.py          # Tournament manager
├── run_experiment.py           # Run individual experiments
├── human_vs_bot.py             # Human vs AI matches
├── concatenate_results.py      # Merge tournament results
│
├── EvalFunction/               # Trained evaluation networks
│
├── results/                    # Tournament outputs
│   ├── combined_statistics/
│   ├── main_tournament_resume/
│   └── ...
│
├── bot_experiments/
│   └── results/                # Archived experiment outputs
│
└── README.md
```

### Main Components

| Component | Description |
|-----------|-------------|
| `bots.py` | Contains implementations of all evaluated agents. |
| `play_tournament.py` | Runs complete tournaments between selected agents and records the results. |
| `run_experiment.py` | Executes predefined experiments and evaluation scenarios. |
| `human_vs_bot.py` | Allows a human player to play against any implemented agent. |
| `concatenate_results.py` | Combines results from multiple tournament runs into aggregated statistics. |
| `EvalFunction/` | Stores trained neural network checkpoints used by neural agents. |
| `results/` | Contains tournament statistics, configuration files, CSV exports, and generated plots. |

## Installation

### Prerequisites

This project depends on the Python environment used by the **EvaluationFunction** module.

Before running experiments, install the dependencies described in `EvaluationFunction/requirements.txt`.

### Running an Experiment

Individual experiments can be started using

```bash
python run_experiment.py
```

To execute a complete tournament between multiple agents, run

```bash
python play_tournament.py
```

Tournament parameters, participating agents, and evaluation settings can be configured directly within the corresponding scripts.
## Running Experiments

Individual bot matchups can be evaluated using:

```bash
python run_experiment.py
```

This script runs a selected pair of agents for a configurable number of games and records information such as:

- winner,
- starting player,
- number of moves,
- game duration,
- moves played,
- final score.

Tournament results are stored in JSON or CSV format so they can be inspected later or combined with other experiment runs.

A complete tournament between multiple agents can be started using:

```bash
python play_tournament.py
```

The tournament script automatically schedules the selected matchups, alternates player positions, saves progress after completed matches, and generates summary statistics and visualizations.

Interrupted tournament runs can be resumed from previously saved results, avoiding the need to repeat already completed games.

To combine multiple experiment outputs into one aggregate report, run:

```bash
python concatenate_results.py
```

## Tournament Configuration

Tournament settings are defined directly in `play_tournament.py` and `run_experiment.py`.

The configurable parameters include:

- participating agents,
- number of games per matchup,
- maximum game length,
- random seed,
- player order,
- checkpoint used by neural agents,
- search depth or number of MCTS simulations,
- output directory.

To reduce first-player bias, agents should play in both player positions. The tournament framework alternates the starting player and evaluates every selected pairing under comparable conditions.

Each tournament run stores its configuration in a `config.json` file together with the generated results. This makes it possible to identify the parameters used for a particular experiment and reproduce the run later.

The output directory typically contains:

```text
config.json             # Tournament configuration
games.csv               # Individual game results
summary.json            # Aggregated statistics
total_scores.png        # Total score comparison
winrate_heatmap.png     # Head-to-head win rates
avg_moves.png           # Average game length
```

## Implemented Agents

The framework contains several agents based on different decision-making approaches.

| Agent | Method | Neural Network |
|------|--------|:--------------:|
| `RandomBot` | Selects a legal move uniformly at random. | No |
| `HeuristicBot` | Evaluates legal moves using a handcrafted heuristic function. | No |
| `NeuralAlphaBetaBot` | Uses alpha-beta search together with the trained neural evaluation network. | Yes |
| `MCTSBot` | Uses Monte Carlo Tree Search to evaluate and select moves. | Yes |

### RandomBot

`RandomBot` serves as the baseline agent. It selects one of the currently legal moves without considering its strategic quality.

### HeuristicBot

`HeuristicBot` evaluates possible moves using manually designed rules and game-specific knowledge. It prioritizes moves that improve the player's position or move the player closer to completing an objective shape.

### NeuralAlphaBetaBot

`NeuralAlphaBetaBot` performs game-tree search using alpha-beta pruning. Leaf positions are evaluated by a trained neural network instead of a handcrafted evaluation function.

The bot can also use the policy output of the network to order candidate moves and improve search efficiency.

### MCTSBot

`MCTSBot` selects moves using Monte Carlo Tree Search. The search repeatedly explores the game tree, evaluates positions, and updates visit statistics.

Its behaviour can be adjusted using parameters such as the number of simulations, exploration constant, and evaluation method.

All agents implement a compatible move-selection interface, allowing them to be exchanged freely in tournament and experiment scripts.

## Output

Each tournament produces a dedicated results directory containing both raw data and aggregated statistics.

Typical outputs include:

| File | Description |
|------|-------------|
| `config.json` | Tournament configuration used for the experiment. |
| `games.csv` | Detailed results of every played game. |
| `summary.json` | Aggregated tournament statistics. |
| `winrate_heatmap.png` | Head-to-head win-rate matrix for all participating agents. |
| `total_scores.png` | Total scores achieved by each agent. |
| `avg_moves.png` | Average number of moves per game. |
| `avg_time.png` | Average decision time per move (when available). |

The generated visualizations provide a concise overview of tournament performance and can be used directly in reports or publications. Multiple tournament runs can be combined into a single summary using `concatenate_results.py`.

## Utility Scripts

Besides the tournament framework, the project includes several helper scripts used during development and experimentation.

| Script | Description |
|---------|-------------|
| `human_vs_bot.py` | Allows a human player to compete against any implemented agent. |
| `concatenate_results.py` | Merges multiple tournament outputs into combined statistics and visualizations. |
| `run_experiment.py` | Executes predefined experimental scenarios. |

These scripts simplify benchmarking, debugging, and result analysis while remaining independent of the core tournament implementation.

## Documentation

Detailed technical documentation is available in the repository-level [`docs/bot-experiments/`](../docs/bot-experiments/) directory.

- [Overview](../docs/bot-experiments/overview.md)  
  Architecture, workflow, project structure, and interaction with other project components.

- [Tournament Framework](../docs/bot-experiments/tournament-framework.md)  
  Match execution, tournament formats, scheduling, resume support, and result generation.

- [Implemented Agents](../docs/bot-experiments/implemented-agents.md)  
  Description of all implemented agents, their decision-making algorithms, and evaluation methodology.

- [Results](../docs/bot-experiments/results.md)  
  Output files, tournament summaries, generated visualizations, and interpretation of experimental results.

## Related Components

This framework is one component of the complete Logix project, which also includes:

- **LogixGame** – a Unity implementation of the Logix board game with support for human and AI players.
- **EvaluationFunction** – a Python framework for training neural network evaluation functions using self-play and Monte Carlo Tree Search.
- **BotExperiments** *(this project)* – an automated benchmarking framework for evaluating and comparing different game-playing agents.
- **BachelorsThesis** – the accompanying thesis describing the design, implementation, training process, and experimental evaluation of the project.

Together, these components provide a complete workflow covering game implementation, artificial intelligence development, experimental evaluation, and documentation.

## Future Work

The experimental framework was designed to be easily extensible. Possible future improvements include:

- support for additional game-playing algorithms,
- integration of Elo rating computation,
- parallel execution of tournament games,
- automated hyperparameter benchmarking,
- statistical significance testing of tournament results,
- expanded visualization and reporting capabilities.

The modular architecture allows new agents to be added with minimal changes to the existing tournament framework.
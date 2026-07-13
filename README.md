# Logix

> A complete framework for the implementation, training, and evaluation of artificial intelligence agents for the board game Logix.

(screenshot)

---

## Overview

This repository contains the complete implementation developed as part of a bachelor's thesis focused on artificial intelligence for the board game **Logix**.

The project consists of four main components:

- a Unity implementation of the game,
- a Python framework for training neural-network-based evaluation functions,
- an experimental framework for benchmarking AI agents,
- the accompanying bachelor's thesis.

Together, these components provide a complete workflow covering game implementation, reinforcement learning, search algorithms, experimental evaluation, and documentation.

## Repository Structure

```
.
├── LogixGame/              # Unity implementation
├── EvaluationFunction/     # Neural network training
├── BotExperiments/         # Tournament framework
├── Builds/                 # Compiled game builds
├── BachelorsThesis/        # Thesis source
└── README.md
```

## Features

- Unity implementation of the Logix board game
- Human vs Human, Human vs AI, and AI vs AI gameplay
- Alpha-Beta and Monte Carlo Tree Search agents
- AlphaZero-inspired reinforcement learning framework
- Neural-network-based position evaluation
- ONNX export for Unity integration
- Automated tournament framework
- Experimental result visualization
- Complete bachelor's thesis

## Screenshots

## Quick Start

### Play the game

Open the Unity project located in `LogixGame/` or download a pre-built executable from the `Builds/` directory.

### Train a neural network

```
cd EvaluationFunction
python train.py
```

### Run tournaments

```
cd BotExperiments
python play_tournament.py
```

## Components

### LogixGame

A Unity implementation of the Logix board game featuring an interactive graphical interface and support for Human vs Human, Human vs AI, and AI vs AI gameplay. The project integrates several search-based artificial intelligence agents, including neural-network-assisted opponents.

For more information, see [LogixGame documentation](LogixGame/README.md)

---

### EvaluationFunction

A Python framework implementing an AlphaZero-inspired reinforcement learning pipeline for training neural-network-based evaluation functions. It includes self-play generation, Monte Carlo Tree Search, replay buffer management, checkpointing, and ONNX model export.

For more information, see [EvaluationFunction documentation](EvaluationFunction/README.md)

---

### BotExperiments

A benchmarking framework used to evaluate and compare different game-playing agents through automated tournaments. It collects detailed performance statistics and generates visualizations used during experimental evaluation.

For more information, see [Open BotExperiments documentation](BotExperiments/README.md)

---

### BachelorsThesis

Contains the complete LaTeX source of the accompanying bachelor's thesis describing the design, implementation, training process, and experimental evaluation of the project.

[Open BachelorsThesis directory](BachelorsThesis/thesis-cs/thesis-cs)

## Technologies

The project combines several technologies across game development, artificial intelligence, and scientific computing.

| Technology | Purpose |
|------------|---------|
| **Unity 6** | Game implementation and graphical user interface |
| **C#** | Gameplay logic and AI integration |
| **Python** | Reinforcement learning framework and experimental evaluation |
| **PyTorch** | Neural network implementation and training |
| **ONNX** | Neural network export for Unity deployment |
| **NumPy** | Numerical computations |
| **Matplotlib** | Visualization of experimental results |
| **Git** | Version control |
| **LaTeX** | Bachelor's thesis preparation |

## Future Work

Although the project provides a complete implementation of the game and several AI agents, there remain numerous opportunities for future development.

Potential directions include:

- stronger neural network architectures,
- distributed self-play training,
- optimization of Monte Carlo Tree Search,
- additional AI agents based on alternative search or learning algorithms,
- online multiplayer support,
- enhanced graphical interface and user experience,
- larger-scale experimental evaluation and automated hyperparameter optimization.

## Author

**František Procházka**

Bachelor's thesis project developed at the Faculty of Mathematics and Physics, Charles University.

The project combines game development, artificial intelligence, reinforcement learning, and experimental evaluation to create a complete environment for developing and benchmarking AI agents for the board game **Logix**.
# Logix Game Overview

[← Back to LogixGame](../../LogixGame/README.md)

## Purpose

**LogixGame** is the Unity implementation of the Logix board game.

It provides a complete graphical user interface, game logic, and player interaction while supporting both human and AI-controlled gameplay. Unlike the Python framework used for training and experiments, the Unity project is intended for playing, demonstrating, and testing the game.

The application supports local multiplayer, games against AI opponents, and fully automated bot-versus-bot matches.

---

## Architecture

The Unity project is organized into several independent subsystems.

```text
Main Menu
      │
      ▼
Game Manager
      │
      ├── Board Logic
      ├── Player Controllers
      ├── AI Controllers
      ├── User Interface
      └── Win Detection
```

Each subsystem is responsible for a separate part of the game while communicating through well-defined interfaces.

---

## Main Components

| Component | Responsibility |
|-----------|----------------|
| `GameManager` | Controls the overall game flow. |
| `GameBoard` | Stores the board state and validates moves. |
| `Player Controllers` | Handle human and AI turns. |
| `Bot Controllers` | Execute AI move selection. |
| `UI System` | Displays menus, inventory, cards, and game information. |
| `WinShape` | Represents objective cards and winning patterns. |

---

## Gameplay Features

The Unity application supports:

- local Player vs Player mode,
- Player vs AI mode,
- AI vs AI demonstrations,
- multiple AI difficulty levels,
- interactive drag-and-click gameplay,
- objective card visualization,
- inventory management,
- rules and information panels,
- game restart and return to the main menu.

---

## AI Integration

The Unity project contains several search-based agents.

Depending on the selected difficulty, the game can use:

- random move selection,
- heuristic evaluation,
- Monte Carlo Tree Search,
- neural-network-assisted search (when available).

The Unity implementation shares the same game rules as the Python training environment to ensure compatibility with trained evaluation functions.

---

## Project Structure

The Unity project follows the standard Unity directory layout.

Important directories include:

| Directory | Purpose |
|-----------|---------|
| `Assets/` | Source code, scenes, prefabs, materials, and UI assets. |
| `Packages/` | Unity package dependencies. |
| `ProjectSettings/` | Unity project configuration. |
| `UserSettings/` | Local editor preferences (not required for gameplay). |

The majority of the gameplay logic is implemented in C# scripts inside the `Assets/` directory.

---

## Relationship to Other Components

The Unity application represents the playable part of the repository.

It interacts with other project components as follows:

### EvaluationFunction

Provides:

- trained neural-network models,
- shared game rules,
- ONNX exports for deployment.

### BotExperiments

Provides:

- evaluation of AI agents,
- tournament statistics,
- performance comparisons.

### BachelorsThesis

Documents the implementation, design decisions, and experimental results.

---

## Design Goals

The Unity implementation was developed with several objectives:

- provide an intuitive graphical interface,
- faithfully implement the Logix rules,
- support multiple gameplay modes,
- allow easy integration of AI agents,
- remain compatible with the Python training environment,
- serve as a demonstration platform for the trained evaluation function.

---

## Related Documentation

- [Architecture](architecture.md)
- [Game Flow](game-flow.md)
- [AI Integration](ai-integration.md)
- [UI System](ui-system.md)
- [Game Rules](../game-rules.md)
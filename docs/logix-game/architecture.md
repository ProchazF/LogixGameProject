# Architecture

[← Back to LogixGame](../../LogixGame/README.md)

## Overview

The Unity project is organized into several independent systems responsible for game logic, player interaction, artificial intelligence, and user interface.

The central component is the `GameManager`, which coordinates all gameplay and communication between the remaining systems.

This modular design keeps the game logic separate from presentation and AI, making the project easier to maintain and extend.

---

## High-Level Architecture

```text
                Main Menu
                    │
                    ▼
              GameManager
                    │
    ┌───────────────┼────────────────┐
    ▼               ▼                ▼
 GameBoard      Player Logic      UI System
    │               │                │
    │               ▼                ▼
    │         Human / AI        Inventory
    │                          Objective Cards
    │                          Menus
    │
    ▼
Win Detection
```

Each subsystem has a clearly defined responsibility and communicates through the game manager.

---

## Core Components

### GameManager

The `GameManager` controls the entire match.

Its responsibilities include:

- initializing a new game,
- creating players,
- assigning objective cards,
- alternating turns,
- validating game progression,
- detecting the winner,
- updating the user interface.

The game manager acts as the central controller of the application.

---

### GameBoard

The `GameBoard` stores the logical board state.

It is responsible for:

- board representation,
- move validation,
- marble placement,
- movement,
- replacement actions,
- board queries,
- win-condition evaluation.

The board implementation is independent of the graphical representation.

---

### Player Controllers

Player controllers determine how moves are selected.

Two controller types are supported:

- human players,
- AI-controlled players.

Both communicate with the game manager through the same interface, allowing different player types to be exchanged without modifying the gameplay loop.

---

### AI Controllers

AI controllers encapsulate the decision-making algorithms.

Depending on the selected difficulty, they may use:

- random move selection,
- heuristic evaluation,
- Monte Carlo Tree Search,
- neural-network-assisted search.

The AI produces only the selected move. Move validation remains the responsibility of the game logic.

---

### User Interface

The UI system visualizes the current game state.

It is responsible for displaying:

- the board,
- player inventories,
- objective cards,
- current player,
- menus,
- rules,
- game results.

The UI reflects the logical state managed by the game manager and does not implement game rules itself.

---

## Scene Structure

The Unity project consists of two primary scenes.

### Main Menu

The main menu allows the player to:

- choose the game mode,
- select AI difficulty,
- open the rules,
- view project information,
- quit the application.

---

### Game Scene

The gameplay scene contains:

- the game board,
- player interface,
- inventory,
- objective cards,
- in-game controls,
- victory screen.

All gameplay takes place within this scene.

---

## Data Flow

During gameplay, information flows through the following pipeline:

```text
Player Input
      │
      ▼
GameManager
      │
      ▼
GameBoard
      │
      ▼
Game State Update
      │
      ▼
User Interface
```

For AI players, the input stage is replaced by an AI controller.

---

## Separation of Responsibilities

The project follows a clear separation between systems.

| System | Responsibility |
|---------|----------------|
| Game logic | Rules and state management |
| AI | Move selection |
| UI | Visualization and user interaction |
| Managers | Overall application flow |

Keeping these responsibilities separate makes the project easier to extend and test.

---

## Extending the Project

New functionality can usually be added without modifying the existing architecture.

Examples include:

- adding new AI agents,
- introducing additional UI panels,
- creating new game modes,
- replacing the AI evaluation function,
- integrating a different neural-network model.

Because each subsystem communicates through well-defined interfaces, changes are generally localized to a single component.

---

## Related Documentation

- [Overview](overview.md)
- [Game Flow](game-flow.md)
- [AI Integration](ai-integration.md)
- [UI System](ui-system.md)
- [Game Rules](../game-rules.md)
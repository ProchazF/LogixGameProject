# UI System

[← Back to LogixGame](../../LogixGame/README.md)

## Overview

The user interface provides all visual interaction with the game while remaining separate from the underlying game logic.

Its primary responsibilities are:

- displaying the current game state,
- handling player input,
- presenting menus and game information,
- visualizing inventories and objective cards,
- communicating game events to the player.

The UI does not implement game rules. Instead, it reflects the logical state maintained by the game manager.

---

## UI Architecture

The interface is built around Unity's Canvas system.

```text
GameManager
      │
      ▼
Game State
      │
      ▼
UI Components
      │
      ├── Board Display
      ├── Inventory
      ├── Objective Cards
      ├── Menus
      └── Game Information
```

Whenever the game state changes, the corresponding UI elements are refreshed.

---

## Main Menu

The main menu is the entry point of the application.

It provides access to:

- game mode selection,
- AI difficulty selection,
- game rules,
- project information,
- application exit.

The menu also serves as the destination when leaving an active match.

---

## Game Interface

During gameplay the interface displays:

- the game board,
- player inventories,
- objective cards,
- current player,
- available controls,
- game status.

The board occupies the central part of the screen, while supporting information is displayed around it.

---

## Board Visualization

The board is represented as a 7×7 grid.

Each occupied cell displays the corresponding marble colour.

The interface updates immediately after every valid move, ensuring that the displayed board always matches the logical game state.

---

## Inventory Display

The shared marble inventory is visualized throughout the match.

The interface displays:

- remaining marbles of each colour,
- selected marble,
- unavailable colours when appropriate.

Inventory changes are reflected immediately after moves are completed.

---

## Objective Cards

Each player is assigned two objective cards.

The interface displays:

- the required winning shape,
- the blocked colour,
- the owning player.

These cards remain visible throughout the game, allowing players to plan their moves without opening additional menus.

---

## Player Interaction

Human players interact with the game using mouse input.

Typical interactions include:

- selecting a marble,
- selecting a board position,
- moving an existing marble,
- replacing an opponent's marble.

The interface forwards these actions to the game logic, which determines whether the move is legal.

---

## Feedback

The interface provides immediate feedback after player actions.

Examples include:

- updating the board,
- refreshing the inventory,
- changing the active player,
- highlighting completed actions,
- displaying the winner when the game ends.

Illegal actions are rejected without modifying the game state.

---

## AI Interaction

During AI turns:

- player input is disabled,
- the bot computes its move,
- the selected move is animated or displayed,
- the interface updates once the move has been applied.

This prevents conflicting user actions while the AI is making its decision.

---

## Rules and Information Panels

The application includes additional interface panels containing:

- game rules,
- project description,
- navigation controls.

These panels can be opened from the main menu and closed without affecting the game.

---

## End of Game

When a winning condition is detected, the interface:

1. announces the winner,
2. disables further gameplay,
3. allows the player to return to the main menu or start a new game.

The board remains visible so the final winning position can be inspected.

---

## Design Principles

The UI was designed with several goals:

- simplicity,
- readability,
- clear separation from game logic,
- minimal player distraction,
- support for both human and AI gameplay.

Game rules remain implemented in the logical layer rather than inside interface components.

---

## Extending the UI

New interface elements can generally be added without modifying the underlying game logic.

Examples include:

- additional animations,
- move history,
- timer display,
- game statistics,
- accessibility options,
- alternative board themes.

Because the UI observes the game state rather than controlling it, most additions remain localized to interface components.

---

## Related Documentation

- [Overview](overview.md)
- [Architecture](architecture.md)
- [Game Flow](game-flow.md)
- [AI Integration](ai-integration.md)
- [Game Rules](../game-rules.md)
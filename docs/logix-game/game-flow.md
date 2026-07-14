# Game Flow

[← Back to LogixGame](../../LogixGame/README.md)

## Overview

The Unity application manages the complete lifecycle of a Logix match, from the main menu to the end-game screen.

The `GameManager` coordinates all gameplay by initializing the board, creating players, processing turns, validating moves, and detecting the winner.

---

## Game Lifecycle

A typical game follows the sequence:

```text
Main Menu
      │
      ▼
Select Game Mode
      │
      ▼
Initialize Match
      │
      ▼
Deal Objective Cards
      │
      ▼
Gameplay Loop
      │
      ▼
Win Detection
      │
      ▼
Game Over
```

Each stage is controlled by the `GameManager`.

---

## Match Initialization

When a new game starts, the manager:

1. Creates a new game board.
2. Places the black marble in the centre.
3. Initializes the shared inventory.
4. Creates the participating players.
5. Assigns objective cards.
6. Sets the starting player.
7. Updates the user interface.

After initialization, the first turn begins immediately.

---

## Turn Structure

Each turn belongs to exactly one player.

The active player may perform one legal action:

- place a marble,
- move an existing marble,
- replace an opponent's marble.

Once a valid move has been executed, the game state is updated and control passes to the opposing player.

---

## Human Turns

During a human turn, the player interacts with the board using the graphical interface.

The player can:

- select marbles from the inventory,
- select marbles already on the board,
- choose destination cells,
- perform replacement actions when allowed.

Only legal actions are accepted by the game logic.

---

## AI Turns

When the active player is controlled by an AI agent:

1. The current game state is passed to the selected bot.
2. The bot computes a move.
3. The move is validated.
4. The board is updated.
5. Control returns to the game manager.

The same validation logic is used for both human and AI players.

---

## Game State Updates

After every move, the game manager updates:

- the board,
- the shared inventory,
- forbidden colours,
- player objectives,
- the active player,
- the graphical interface.

The board displayed to the player always reflects the current logical game state.

---

## Win Detection

After each move, the game checks whether the active player has completed one of their assigned objective shapes.

If a valid winning shape is detected:

1. the match ends,
2. the winner is announced,
3. further moves are disabled.

If no winner exists, play continues with the next turn.

---

## Supported Game Modes

The Unity application supports three gameplay modes.

### Player vs Player

Both players are controlled by humans using the same computer.

---

### Player vs AI

One player is controlled by a human, while the opponent uses one of the available AI agents.

The AI difficulty determines the selected search algorithm or search budget.

---

### AI vs AI

Both players are controlled by AI agents.

This mode is useful for demonstrations and visual inspection of agent behaviour.

---

## Returning to the Main Menu

The game can be exited at any time using the in-game **Main Menu** button.

Returning to the menu terminates the current match and resets the game state before a new game can be started.

---

## Error Handling

The game manager validates every move before applying it.

Illegal actions are rejected and the current player must select another move.

This guarantees that the graphical interface cannot produce an invalid game state.

---

## Related Documentation

- [Overview](overview.md)
- [Architecture](architecture.md)
- [AI Integration](ai-integration.md)
- [UI System](ui-system.md)
- [Game Rules](../game-rules.md)
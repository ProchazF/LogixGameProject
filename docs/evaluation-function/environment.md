# Game Environment

[← Back to EvaluationFunction](../../EvaluationFunction/README.md)

## Overview

The game environment implements the complete rules and state transitions of **Logix** independently of the Unity application.

Its main purpose is to provide a deterministic and reproducible simulation environment for:

- reinforcement learning,
- Monte Carlo Tree Search,
- Alpha-Beta search,
- automated experiments,
- human game recording,
- model inference.

The main environment used during training and experiments is the `LogixShapeEnv` class defined in `env_logix_helper.py`.

---

## Main Environment Class

### `LogixShapeEnv`

`LogixShapeEnv` stores the complete game state and provides methods for generating legal moves, applying actions, simulating successor states, and detecting terminal positions.

A typical environment is created using:

```python
env = LogixShapeEnv(
    n=7,
    max_game_len=100,
    seed=None,
)
```

The standard board size is fixed to `7 × 7`.

The environment uses two players represented by:

```text
+1  first player
-1  second player
```

The `player` attribute always identifies the player whose turn is currently active.

---

## Responsibilities

The environment is responsible for:

- storing the board state,
- tracking the active player,
- managing the shared inventory,
- storing player objective cards,
- maintaining forbidden colours,
- remembering colours used in the previous move,
- generating legal actions,
- validating placement, movement, and replacement moves,
- applying actions,
- detecting winning shapes,
- tracking the turn count,
- terminating games that exceed the maximum length,
- creating independent successor states for search algorithms.

---

## Internal State

A complete game state includes the following information.

| Attribute | Description |
|---|---|
| `board` | `7 × 7` array storing coloured marbles |
| black-marble state | Separate representation of the black marble |
| `player` | Current player, represented by `+1` or `-1` |
| `turn` | Current turn counter |
| inventory | Shared number of available marbles for each colour |
| forbidden colours | Colours unavailable to the current player |
| `last_colors_played` | Colours involved in the previous move |
| player objectives | Winning shapes assigned to each player |
| maximum game length | Maximum number of moves before a draw |

The state is fully independent of any graphical representation.

---

## Board Representation

The logical board has shape:

```text
(7, 7)
```

Standard coloured marbles are stored using integer codes.

The playable colours are:

| Code | Colour |
|---:|---|
| `1` | Red |
| `2` | Green |
| `3` | Blue |
| `4` | Yellow |
| `5` | Grey |

The black marble is represented separately in the live environment and is encoded using its own plane when the state is passed to the neural network.

Empty cells are represented by:

```text
0
```

The exact snapshot representation may encode the black marble using a dedicated numeric value for serialization.

---

## Initial State

At the beginning of a game:

- the board is empty,
- the black marble is placed in the centre,
- the current player is initialized,
- the shared inventory is reset,
- no colours are forbidden,
- `last_colors_played` is empty,
- each player receives objective cards,
- the turn counter is set to zero.

For a `7 × 7` board, the initial black-marble position is:

```text
row = 3
column = 3
```

using zero-based indexing.

---

## Shared Inventory

The inventory is shared by both players.

It stores the remaining number of marbles for each playable colour.

The available inventory colours are:

```text
Red
Green
Blue
Yellow
Grey
```

Placement and replacement actions consume marbles from the inventory.

Movement actions do not consume inventory because an existing marble is only relocated.

When a replacement removes a marble from the board, the corresponding inventory values are updated according to the game rules implemented by the environment.

The environment includes consistency checks to ensure that board contents and inventory values remain valid.

---

## Forbidden Colours

The environment maintains a set of colours that cannot be used during the current turn.

The forbidden set is derived from the colours used in the previous move.

The method:

```python
env.banned_colors()
```

returns the currently forbidden colours.

The update depends on the action type:

- placement records the placed colour,
- movement records the moved marble's colour,
- replacement records both the removed and inserted colours.

Grey may also become forbidden when it participates in a move.

The forbidden set is global for the current turn rather than being stored separately for each player.

---

## Supported Actions

The environment supports three move categories:

1. placement,
2. movement,
3. replacement.

All legal actions are returned using a consistent tuple-based representation.

The exact tuple structure is interpreted by the action encoder and environment methods.

---

## Placement

A placement action adds a marble from the shared inventory to an empty cell.

A placement is legal only when:

- the destination cell is empty,
- the selected colour is available in the inventory,
- the selected colour is not forbidden,
- the destination is orthogonally adjacent to at least one occupied cell.

Orthogonal adjacency means sharing an edge.

```text
    X
  X C X
    X
```

Diagonal adjacency alone is not sufficient.

The initial black marble guarantees that legal placement cells exist at the beginning of the game.

---

## Movement

A movement action relocates an existing marble.

The black marble may also be moved when the movement rules permit it.

A movement is legal only when:

- the source cell contains a movable marble,
- the source marble is not completely blocked,
- the destination cell is empty,
- the destination is reachable through empty cells,
- reachability uses four-directional connectivity,
- the destination is adjacent to the occupied structure,
- the original source cell is treated as empty during validation,
- the move does not create an invalid floating position.

The environment uses a breadth-first search over empty cells to determine whether the destination is reachable from the source.

The source marble cannot move through occupied cells.

---

## Movement Reachability

Movement is based on connectivity through empty cells.

The search considers only:

```text
up
down
left
right
```

Diagonal movement is not supported.

A destination may be geographically close to the source but still illegal if no valid empty-cell path exists.

Solid occupied barriers can therefore prevent movement between different parts of the board.

---

## Source Blocking

A marble cannot be moved when every orthogonally adjacent cell is blocked.

Before testing reachable destinations, the environment checks whether the source marble has access to at least one empty neighboring cell.

This avoids unnecessary path searches and prevents impossible moves from being generated.

---

## Destination Adjacency

The movement destination must remain adjacent to the occupied board structure.

When this condition is checked, the source cell is excluded because the marble is assumed to have already left it.

This detail is important. Without excluding the original source, a destination could appear connected only because it is adjacent to a cell that becomes empty after the move.

---

## Replacement

A replacement action removes a marble from the board and inserts another colour at the same position.

A replacement is legal only when:

- the target can legally be replaced,
- the replacement colour is available,
- the replacement colour is not forbidden,
- the replacement satisfies the environment's colour restrictions,
- the inventory can be updated consistently.

After the move:

- the inserted marble is removed from inventory,
- the removed colour is returned or updated according to the implemented rule,
- both involved colours are recorded in `last_colors_played`,
- both colours may become forbidden for the next player.

---

## Legal Move Generation

The method:

```python
env.legal_moves()
```

returns all actions legal in the current state.

The method considers:

- board occupancy,
- inventory availability,
- forbidden colours,
- movement reachability,
- source blocking,
- destination adjacency,
- replacement legality,
- current game status.

Search algorithms and bots are expected to select actions only from this list.

A legal-move list may contain actions from all three categories at the same time.

---

## Executing a Move

Moves are executed using:

```python
next_state, done, result = env.step(move)
```

The method:

1. validates or applies the supplied move,
2. updates the board,
3. updates the inventory,
4. updates forbidden colours,
5. updates `last_colors_played`,
6. increments the turn counter,
7. checks for a winning shape,
8. checks the maximum game length,
9. changes the active player when the game continues.

The returned values are:

| Value | Meaning |
|---|---|
| `next_state` | Updated state representation |
| `done` | Whether the game has ended |
| `result` | Final game result or current non-terminal value |

---

## Result Convention

Terminal results are represented using:

```text
+1  first player wins
 0  draw
-1  second player wins
```

During neural-network training, results may later be converted to the perspective of the player associated with a stored state.

This perspective conversion is important for value-target generation.

---

## Maximum Game Length

The environment accepts a configurable maximum game length.

For example:

```python
env = LogixShapeEnv(max_game_len=100)
```

When the turn limit is reached without a winner, the game terminates as a draw.

This prevents self-play and tournaments from becoming indefinitely long.

---

## Win Detection

After each move, the environment checks whether the active player has completed one of their assigned objective shapes.

A valid winning shape must satisfy the shared game rules, including:

- matching an assigned objective,
- allowing rotation,
- disallowing unsupported mirroring,
- containing the black marble,
- using one consistent standard colour,
- allowing grey wildcard marbles,
- respecting the card's blocked colour,
- satisfying the exact five-marble component rule.

Detailed rules are described in:

```text
docs/game-rules.md
```

---

## Objective Cards

Each player receives a collection of objective shapes.

The environment stores these objectives as part of the game state so they can be used by:

- win detection,
- state encoding,
- neural-network evaluation,
- self-play,
- experiments.

Objective data must be serializable because it may appear inside stored state snapshots and replay-buffer samples.

---

## State Snapshots

Search, replay storage, and model input require stable snapshots of the environment.

A state snapshot includes:

- board contents,
- black-marble position,
- current player,
- turn number,
- forbidden-colour mask,
- inventory values,
- objective definitions.

Snapshots must be independent of future environment mutation.

This prevents previously stored states from changing when the live game continues.

---

## Move Simulation

Search algorithms need to inspect successor states without modifying the original environment.

The environment therefore supports simulated moves using a copied state.

A typical pattern is:

```python
child_env = env.simulate_move(move)
```

or an equivalent deep-copy-based implementation.

Simulation is used by:

- Monte Carlo Tree Search,
- Alpha-Beta search,
- tactical move checks,
- bot evaluation,
- testing.

The original environment must remain unchanged after simulation.

---

## Resetting the Environment

A new game is initialized using:

```python
env.reset()
```

Resetting restores:

- the initial board,
- centre black marble,
- inventory,
- player turn,
- objective assignments,
- forbidden colours,
- previous-move information,
- turn counter,
- terminal status.

Training code should call `reset()` before generating each new self-play game.

---

## Randomness and Seeds

The environment accepts an optional random seed.

```python
env = LogixShapeEnv(seed=42)
```

Randomness may affect:

- objective-card assignment,
- randomized agent behavior,
- self-play exploration,
- experiment reproducibility.

Using fixed seeds makes debugging and experimental comparison easier.

A seed does not make neural-network execution fully deterministic unless all relevant PyTorch and hardware settings are also configured accordingly.

---

## Main Public Interface

| Method or attribute | Description |
|---|---|
| `reset()` | Initializes a new game |
| `legal_moves()` | Returns all currently legal actions |
| `step(move)` | Applies a move and advances the game |
| `simulate_move(move)` | Creates a successor state without mutating the original |
| `banned_colors()` | Returns the current forbidden-colour set |
| `player` | Active player represented by `+1` or `-1` |
| `board` | Current `7 × 7` board state |
| `turn` | Current move counter |

Only the important public interface is documented here. Internal helper methods are implementation details and should be documented directly in the source code when their behaviour is non-obvious.

---

## Environment Consumers

The environment is used by several parts of the repository.

### Training

`selfplay.py` repeatedly creates environments and uses MCTS to generate games.

### Monte Carlo Tree Search

`mcts.py` calls legal move generation and successor-state simulation during each search.

### Bot Experiments

The tournament scripts use the same environment to evaluate agents under identical rules.

### Human Recording

Human-game recording tools use the environment to validate and store manually played games.

### Debugging Tools

GUI and position-printing scripts use the environment to inspect legal and illegal moves visually.

---

## Error Handling

Bots should only return moves generated by:

```python
env.legal_moves()
```

Experiment scripts may detect an illegal bot action and replace it with a fallback legal move to keep a tournament running.

Such behavior is intended for robustness and debugging. It should not hide repeated errors in an agent implementation.

When no legal move exists, the environment or caller must handle the situation explicitly rather than indexing an empty list.

---

## Consistency with Unity

The Python environment and Unity game implement the same rules independently.

The following details must remain synchronized:

- coordinate conventions,
- colour mapping,
- inventory changes,
- forbidden-colour behavior,
- placement adjacency,
- movement reachability,
- replacement behavior,
- objective transformations,
- grey wildcard handling,
- black-marble handling,
- win detection,
- game termination.

A rule discrepancy can cause a neural network to learn behavior that is illegal or incorrect in the Unity application.

---

## Testing Priorities

The most important environment behaviors to test are:

- initial state creation,
- legal placement generation,
- forbidden-colour updates,
- movement through connected empty regions,
- movement blocked by occupied barriers,
- source-cell exclusion during movement validation,
- inventory updates,
- replacement restrictions,
- black-marble movement,
- exact shape validation,
- draw termination,
- simulation not mutating the original environment.

Tests should focus on rule edge cases rather than only typical game positions.

---

## Related Documentation

- [Game Rules](../game-rules.md)
- [State and Action Encoding](state-and-action-encoding.md)
- [MCTS and Self-Play](mcts-and-self-play.md)
- [Training](training.md)
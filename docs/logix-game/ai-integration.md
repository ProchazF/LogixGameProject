# AI Integration

[← Back to LogixGame](../../LogixGame/README.md)

## Overview

The Unity application supports multiple computer-controlled players through a common AI integration layer.

AI agents are responsible only for selecting moves. The authoritative game state, move validation, turn handling, and win detection remain inside the standard game logic.

This separation ensures that human players and AI players follow the same rules and use the same move-execution pipeline.

---

## AI Workflow

A typical AI turn follows this sequence:

```text
GameManager
      │
      ▼
AI Player Controller
      │
      ▼
Create Current Game State
      │
      ▼
Bot Selects Move
      │
      ▼
GameBoard Validates Move
      │
      ▼
Move Is Applied
      │
      ▼
GameManager Continues Match
```

The AI never modifies the board directly.

Instead, it returns a move that is processed by the same game systems used for human input.

---

## Main Responsibilities

The AI integration layer is responsible for:

- selecting the correct bot for the chosen game mode,
- passing the current game state to the bot,
- requesting a move,
- waiting for the bot to finish,
- returning the move to the game manager,
- preventing additional player input during AI computation,
- updating the interface after the move is applied.

---

## Game Modes

AI agents are used in two game modes.

### Player vs AI

One player is controlled by a human and the other by a bot.

The selected difficulty determines which bot configuration is used.

### AI vs AI

Both players are controlled by bots.

This mode can be used to:

- observe agent behaviour,
- compare different strategies,
- demonstrate automated gameplay,
- test the stability of the game loop.

---

## Common Bot Interface

All bots should expose a compatible move-selection interface.

Conceptually:

```csharp
Move ChooseMove(GameBoard board);
```

or an asynchronous equivalent.

The bot receives access to the current logical state and returns one candidate move.

A bot implementation should not:

- directly update scene objects,
- modify UI elements,
- bypass move validation,
- advance the turn itself.

Those responsibilities remain with the game manager and board logic.

---

## Available AI Approaches

The Unity project can support several types of agents.

### Random Bot

The random bot selects one legal move without evaluating its strategic quality.

It is useful for:

- debugging,
- baseline difficulty,
- fast automated matches,
- testing legal-move generation.

### Heuristic Bot

The heuristic bot scores candidate moves using manually designed game knowledge.

Typical considerations may include:

- immediate wins,
- progress toward objective shapes,
- blocking opponent threats,
- useful positions around the black marble.

### Alpha-Beta Bot

The alpha-beta bot searches the game tree to a limited depth.

Leaf positions are evaluated using either:

- a handcrafted evaluation function,
- a neural-network evaluation function.

Move ordering can significantly improve pruning efficiency.

### MCTS Bot

The Monte Carlo Tree Search bot explores possible continuations using repeated simulations.

Its strength and execution time depend mainly on:

- number of iterations,
- exploration settings,
- evaluation method,
- tree reuse.

### Neural-Network-Assisted Bot

A trained neural network can provide:

- policy estimates for promising moves,
- value estimates for position quality.

The model is trained in the Python `EvaluationFunction` component and exported to ONNX for use in Unity.

---

## Difficulty Selection

Difficulty levels map user-facing options to bot configurations.

A typical configuration may use:

| Difficulty | Behaviour |
|---|---|
| Easy | Random or low-budget search |
| Normal | Moderate search budget |
| Hard | Larger search budget or stronger evaluation |

The exact mapping is controlled by the game configuration and bot initialization code.

Difficulty should affect the AI configuration rather than the game rules.

---

## AI Turn Handling

When an AI turn begins, the game manager should:

1. disable human board input,
2. indicate that the bot is thinking,
3. pass a stable game state to the bot,
4. wait for the selected move,
5. validate the returned move,
6. apply the move,
7. update the board and UI,
8. re-enable input if the next player is human.

Buttons and board controls should remain disabled while the bot is computing to prevent conflicting actions.

---

## Synchronous and Asynchronous Execution

Simple bots can execute immediately on the Unity main thread.

More expensive bots, such as MCTS or neural-search agents, may take long enough to freeze the interface.

Long-running calculations should therefore be handled carefully.

Possible approaches include:

- coroutines,
- asynchronous tasks,
- worker threads,
- splitting work across frames.

Unity scene objects and most Unity APIs must still be updated on the main thread.

A background calculation should therefore return only plain game data, such as a `Move`, before the game manager updates the scene.

---

## State Copying

Search algorithms must evaluate hypothetical moves without modifying the live match.

The AI should use:

- copied board states,
- simulated game states,
- immutable snapshots.

A simulated branch must not alter:

- the visible board,
- current inventory,
- player objectives,
- active player,
- forbidden colours.

Incorrect state sharing can corrupt both the search and the running game.

---

## Legal Move Validation

Bots should choose from the currently legal move set.

Conceptually:

```csharp
List<Move> legalMoves = board.GetLegalMoves(currentPlayer);
```

The selected move is validated again before execution.

This defensive validation protects the game against:

- stale AI state,
- search bugs,
- encoding mistakes,
- invalid model output.

If the move is illegal, the game should report the error and avoid silently corrupting the state.

---

## ONNX Model Integration

The trained network is exported from Python using:

```bash
python export_onnx.py
```

The exported model contains two outputs:

- policy logits,
- position value.

Expected input dimensions are:

```text
board input:    (batch, 6, 7, 7)
feature input:  (batch, 99)
```

Expected output dimensions are:

```text
policy output:  (batch, 2891)
value output:   (batch, 1)
```

The Unity implementation must reproduce the Python state encoding exactly.

---

## Encoding Compatibility

The following definitions must match between Python and Unity:

- colour-plane order,
- board-coordinate convention,
- inventory feature order,
- forbidden-colour order,
- objective-card encoding,
- current-player representation,
- action indexing,
- policy-output offsets.

A model can load successfully while still producing incorrect results if the semantic order of features differs.

Cross-platform validation should compare both implementations on the same game state.

---

## Policy Output

The policy head returns one score for every encoded action.

The action space contains:

| Action category | Count |
|---|---:|
| Placement | 245 |
| Movement | 2401 |
| Replacement | 245 |
| **Total** | **2891** |

Unity must apply a legal-action mask before interpreting the policy.

Illegal moves must receive zero probability or be excluded from selection.

---

## Value Output

The value head predicts the expected result of the current position.

The value convention must match the Python implementation.

Typically:

```text
+1  favourable for the active player
 0  approximately equal
-1  unfavourable for the active player
```

Search code must convert perspectives consistently when turns alternate.

---

## Model Placement

Exported models should be stored inside an appropriate Unity asset directory, for example:

```text
Assets/Models/
```

or another project-specific resources directory.

The model must be imported by Unity and assigned to the component responsible for neural inference.

The exact location is less important than keeping the path stable and documenting which checkpoint produced the model.

---

## Model Loading

The neural bot should load the model once during initialization.

The model should not be reloaded before every move because repeated loading would significantly increase execution time.

A typical lifecycle is:

```text
Scene starts
      │
      ▼
Load model
      │
      ▼
Create inference worker
      │
      ▼
Reuse worker for all AI turns
      │
      ▼
Dispose worker when finished
```

The exact API depends on the neural-network package used by the Unity version.

---

## Inference Pipeline

A neural evaluation typically performs:

1. create the board tensor,
2. create the feature tensor,
3. run model inference,
4. read policy logits,
5. read the value output,
6. mask illegal actions,
7. pass results to the search algorithm.

Conceptually:

```text
GameBoard
    │
    ▼
Unity State Encoder
    │
    ▼
ONNX Model
    │
    ├── Policy
    └── Value
```

The neural network should generally guide a search algorithm rather than directly selecting the highest-logit move.

---

## Search Integration

### Neural Alpha-Beta

The value output can evaluate leaf states.

The policy output can order legal moves before search.

This may improve pruning by exploring promising actions first.

### Neural MCTS

The policy output initializes action priors.

The value output evaluates newly expanded nodes.

This avoids random rollouts and matches the training framework more closely.

---

## Bot Configuration

Bot-specific parameters should be stored in a clear configuration object or serialized Unity fields.

Typical parameters include:

- search depth,
- MCTS iteration count,
- exploration constant,
- model asset,
- move delay,
- deterministic or stochastic selection.

Exposing these fields in the Inspector makes it easier to tune difficulty without modifying source code.

---

## Visual Delay

AI vs AI games may complete too quickly for a human observer to follow.

A configurable delay can be added between moves.

This delay should affect only presentation, not search computation or game logic.

For example:

```text
0 seconds    fast automated testing
0.5 seconds  visible demonstration
1 second     slower explanatory playback
```

---

## Error Handling

The AI layer should explicitly handle:

- no legal moves,
- invalid returned moves,
- missing model assets,
- incompatible tensor dimensions,
- failed inference,
- non-finite model outputs,
- cancelled asynchronous tasks.

A safe fallback may select a legal move to keep a demonstration running, but the original error should still be logged.

Fallback behaviour should not be used silently in experimental evaluation.

---

## Adding a New Bot

A new Unity bot should:

1. implement the common bot interface,
2. receive the current game state,
3. generate or inspect legal moves,
4. avoid modifying the live state during search,
5. return one legal move,
6. support cancellation or delayed execution when needed.

A minimal conceptual example is:

```csharp
public class ExampleBot : IBot
{
    public Move ChooseMove(GameBoard board)
    {
        List<Move> legalMoves = board.GetLegalMoves();

        if (legalMoves.Count == 0)
        {
            return null;
        }

        return legalMoves[0];
    }
}
```

The actual interface should follow the existing project code.

---

## Testing AI Integration

Important tests include:

- AI turns start automatically,
- human input is disabled during bot computation,
- every returned move is legal,
- bot simulation does not modify the live board,
- both player slots can use bots,
- difficulty settings create the intended bot,
- missing models produce a clear error,
- repeated games do not leak inference workers,
- returning to the main menu cancels unfinished bot work.

Constructed tactical positions are useful for testing whether a bot detects immediate winning moves.

---

## Relationship to Python Agents

The Unity bots and Python bots may implement similar algorithms, but they are separate implementations.

They should share:

- game rules,
- state semantics,
- action semantics,
- model interfaces.

They do not need to share identical internal code.

The Python version is used primarily for training and automated experiments, while the Unity version is used for interactive gameplay and demonstration.

---

## Related Documentation

- [Logix Game Overview](overview.md)
- [Architecture](architecture.md)
- [Game Flow](game-flow.md)
- [UI System](ui-system.md)
- [State and Action Encoding](../evaluation-function/state-and-action-encoding.md)
- [Neural Network](../evaluation-function/neural-network.md)
- [Game Rules](../game-rules.md)
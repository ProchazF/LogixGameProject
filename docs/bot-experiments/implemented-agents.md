# Implemented Agents

[← Back to BotExperiments](../../BotExperiments/README.md)

## Overview

The `BotExperiments` module contains several Logix-playing agents based on different decision-making strategies.

All agents are implemented in:

```text
BotExperiments/bots.py
```

and expose a compatible move-selection interface:

```python
move = bot.choose_move(environment)
```

The returned move must be legal in the current environment state.

This shared interface allows the tournament framework to compare agents without changing the match runner.

---

## Agent Summary

| Agent | Main Method | Neural Network | Typical Strength | Typical Speed |
|---|---|:---:|---|---|
| `RandomBot` | Random legal move | No | Low | Very fast |
| `HeuristicBot` | Handcrafted move evaluation | No | Strong baseline | Fast |
| `NeuralAlphaBetaBot` | Alpha-beta search with learned evaluation | Yes | Medium to strong | Slower |
| `MCTSBot` | Monte Carlo Tree Search | Optional or configuration-dependent | Medium to strong | Configurable |

The exact performance depends on search parameters, checkpoint quality, and the number of games used during evaluation.

---

## Common Agent Interface

Every automated agent must provide a method compatible with:

```python
def choose_move(self, env):
    ...
```

The method receives the current `LogixShapeEnv` instance and returns one move from:

```python
env.legal_moves()
```

A bot should not modify the original environment while evaluating candidate actions unless the move is actually selected.

Search-based bots should use copied or simulated successor states.

---

## `RandomBot`

`RandomBot` selects one legal action uniformly at random.

Conceptually:

```python
legal_moves = env.legal_moves()
move = random.choice(legal_moves)
```

### Purpose

The random agent serves as the simplest baseline in experiments.

It is useful for:

- checking that stronger agents outperform chance,
- validating the tournament framework,
- measuring the basic difficulty of the game,
- quickly testing environment stability.

### Characteristics

- no lookahead,
- no position evaluation,
- very low computational cost,
- high variability between games,
- weak strategic performance.

### Limitations

The agent does not:

- detect threats,
- prioritize winning moves,
- consider objective shapes,
- account for future consequences.

Despite its simplicity, it is an important control baseline.

---

## `HeuristicBot`

`HeuristicBot` evaluates candidate moves using a handcrafted scoring function.

The heuristic estimates whether a move improves the player's position according to selected game-specific criteria.

Possible evaluation factors include:

- immediate winning opportunities,
- progress toward objective shapes,
- blocking opponent threats,
- use of strategically useful colours,
- board connectivity,
- position around the black marble.

The exact scoring logic is defined in `bots.py`.

### Decision Process

A typical decision process is:

1. Generate all legal moves.
2. Check whether any move wins immediately.
3. Simulate each candidate move.
4. evaluate the resulting position,
5. select the move with the highest score.

Conceptually:

```python
best_move = None
best_score = float("-inf")

for move in env.legal_moves():
    child = env.simulate_move(move)
    score = evaluate(child)

    if score > best_score:
        best_score = score
        best_move = move
```

### Purpose

The heuristic agent serves as a strong non-neural baseline.

It is useful for determining whether more expensive search methods provide a meaningful improvement over manually designed strategy.

### Characteristics

- deterministic or nearly deterministic,
- fast compared with deeper search,
- interpretable decision logic,
- dependent on manually chosen evaluation criteria.

### Limitations

Its strength is limited by the quality of the handcrafted evaluation function.

The heuristic may perform well in situations anticipated by its designer while failing in unfamiliar positions.

---

## `NeuralAlphaBetaBot`

`NeuralAlphaBetaBot` combines game-tree search with a trained neural-network evaluation function.

Instead of evaluating leaf states using only handcrafted rules, the bot loads a PyTorch checkpoint and uses the network value output to estimate position quality.

The agent may also use policy predictions to order moves before search.

### Main Dependencies

The bot depends on:

- `LogixShapeEnv`,
- state encoding,
- action encoding,
- the trained `LogixNet`,
- a compatible PyTorch checkpoint.

Typical checkpoints are stored in:

```text
BotExperiments/EvalFunction/
```

or loaded from:

```text
EvaluationFunction/checkpoints/
```

### Decision Process

A typical move-selection process is:

1. Generate legal moves.
2. Detect immediate winning moves.
3. Order moves using network policy scores.
4. Search candidate moves using alpha-beta pruning.
5. Evaluate leaf states using the network value head.
6. Return the best move.

### Alpha-Beta Search

Alpha-beta pruning avoids exploring branches that cannot affect the final decision.

The bot searches to a configured depth and maintains:

```text
alpha = best guaranteed value for the maximizing player
beta  = best guaranteed value for the minimizing player
```

A branch may be skipped when:

```text
alpha >= beta
```

Move ordering is especially important because good ordering increases the amount of pruning.

### Neural Evaluation

At a leaf state, the bot:

1. encodes the game state,
2. passes it through the network,
3. reads the scalar value prediction,
4. converts the value to the required search perspective.

The value convention must match the network training convention.

### Policy-Based Move Ordering

The policy output can be used to order legal actions from most promising to least promising.

This does not directly determine the selected move, but it may improve alpha-beta efficiency by causing strong moves to be searched first.

### Caching

The bot may cache network evaluations or policy values.

Cache keys must be immutable and uniquely represent the full state.

Mutable structures such as lists cannot be used directly as dictionary keys.

### Characteristics

- uses learned position evaluation,
- benefits from stronger checkpoints,
- can search tactically beyond the raw network prediction,
- slower than heuristic evaluation,
- sensitive to search depth and move ordering.

### Limitations

The agent depends on:

- checkpoint quality,
- encoding compatibility,
- correct value perspective,
- neural-inference speed.

A deeper search is not always practical because the Logix branching factor can be large.

---

## `MCTSBot`

`MCTSBot` selects moves using Monte Carlo Tree Search.

The agent repeatedly explores possible continuations and uses accumulated search statistics to choose the final action.

Depending on its configuration, leaf positions may be evaluated using:

- random simulations,
- tactical rules,
- a heuristic,
- a neural network.

The implementation used in `BotExperiments` should be treated according to its current constructor and configuration in `bots.py`.

### Search Process

Each simulation generally performs:

1. selection,
2. expansion,
3. evaluation,
4. backpropagation.

After the configured number of simulations, the root action with the strongest visit statistics is selected.

### Selection

The search balances:

- exploitation of actions with strong estimated results,
- exploration of actions that have been visited less often.

A UCT- or PUCT-style formula is typically used.

### Evaluation

The evaluation method determines the character of the agent.

Random playout evaluation is simple but noisy.

Neural evaluation is more informed but requires model inference.

A tactical implementation may also check immediate winning moves before or during search.

### Main Parameters

Typical parameters include:

| Parameter | Meaning |
|---|---|
| `simulations` or `iterations` | Search simulations performed per move |
| exploration constant | Strength of exploration |
| checkpoint path | Neural model used when applicable |
| device | CPU or CUDA inference device |
| maximum rollout depth | Limit for simulation-based evaluation |

The exact parameter names are defined by the implementation.

### Characteristics

- scalable search budget,
- does not require fixed-depth exploration,
- suitable for large branching factors,
- strength increases with more simulations,
- slower when given a large search budget.

### Limitations

MCTS performance depends strongly on:

- the evaluation method,
- simulation count,
- exploration settings,
- search-tree reuse,
- legal-move generation speed.

A small search budget may produce unstable decisions, while a very large budget significantly increases tournament duration.

---

## Immediate Win Detection

Several agents may perform a tactical check before their main decision procedure.

The bot simulates each legal move and checks whether it immediately ends the game in the active player's favour.

Conceptually:

```python
for move in env.legal_moves():
    child = env.simulate_move(move)

    if child_is_winning:
        return move
```

This prevents an otherwise approximate search or evaluation method from overlooking a one-move victory.

Immediate win detection should use the environment's authoritative win-checking logic.

---

## Illegal-Move Handling

Agents are expected to return legal actions.

The experiment runner may include a defensive fallback:

```python
if move not in env.legal_moves():
    move = env.legal_moves()[0]
```

This prevents a long-running tournament from terminating because of one invalid move.

However, illegal moves indicate a bot defect and should be reported clearly.

Repeated fallback use makes experimental results unreliable because the agent is no longer being evaluated according to its intended algorithm.

---

## Determinism

Agent reproducibility depends on the method used.

### RandomBot

Requires a fixed random seed for repeatable move selection.

### HeuristicBot

Usually deterministic unless random tie-breaking is used.

### NeuralAlphaBetaBot

Usually deterministic when:

- the model is in evaluation mode,
- move ordering is deterministic,
- ties are resolved consistently.

Small numerical differences may still occur between CPU and GPU execution.

### MCTSBot

May be stochastic when it uses:

- random rollouts,
- random expansion,
- root noise,
- random tie-breaking.

For controlled tournaments, random seeds should be recorded.

---

## Performance Considerations

The agents have very different computational requirements.

### Fast Agents

`RandomBot` and `HeuristicBot` can usually evaluate moves quickly.

They are suitable for:

- environment testing,
- large baseline tournaments,
- fast regression checks.

### Search-Based Agents

`NeuralAlphaBetaBot` and `MCTSBot` may require substantially more time.

Their cost depends on:

- legal-move count,
- search depth,
- number of simulations,
- model inference time,
- state-copying performance,
- caching efficiency.

Tournament configurations should avoid giving different agents unintentionally unequal computational budgets unless that difference is part of the experiment.

---

## Neural Checkpoint Compatibility

A neural agent requires a checkpoint compatible with the current implementation.

The following must match:

```text
board channels = 6
feature dimension = 99
policy size = 2891
network architecture
state encoding
action encoding
```

A checkpoint may load unsuccessfully when tensor dimensions differ.

More dangerously, it may load successfully but behave incorrectly when feature ordering or action interpretation has changed.

---

## Adding a New Agent

A new agent should be added to `bots.py`.

At minimum, it must:

1. provide a constructor,
2. implement `choose_move(env)`,
3. return a legal move,
4. avoid mutating the live environment during evaluation,
5. handle terminal or empty-move states safely.

A minimal example is:

```python
class ExampleBot:
    def __init__(self, name="ExampleBot"):
        self.name = name

    def choose_move(self, env):
        legal_moves = env.legal_moves()

        if not legal_moves:
            raise RuntimeError("No legal moves available.")

        return legal_moves[0]
```

The bot can then be registered in `run_experiment.py` or `play_tournament.py`.

---

## Recommended Bot Metadata

For clearer tournament outputs, each bot should expose or be assigned:

- a unique display name,
- algorithm type,
- parameter configuration,
- checkpoint identifier when applicable.

For example:

```text
MCTS_1000
NeuralAlphaBeta_depth2_net015200
Heuristic_v2
Random_seed42
```

Descriptive names make result files easier to interpret later.

---

## Agent Evaluation

Agents should be compared using multiple metrics.

Useful metrics include:

- win rate,
- loss rate,
- draw rate,
- total score,
- average game length,
- average move time,
- head-to-head performance.

A single matchup may not fully describe agent quality.

For example, one bot may perform well against random play but poorly against a tactical heuristic.

Round-robin evaluation provides a broader comparison.

---

## Fair Comparison Guidelines

For reliable experiments:

- alternate player positions,
- use the same maximum game length,
- record random seeds,
- use the same environment version,
- use equal search budgets when appropriate,
- identify checkpoint versions,
- repeat enough games to reduce variance.

Search-budget equality should be interpreted carefully because one alpha-beta node and one MCTS simulation do not have identical computational cost.

Wall-clock limits may sometimes provide a fairer comparison than equal iteration counts.

---

## Known Experimental Ordering

In the experiments associated with the project, the observed overall ordering was approximately:

```text
Heuristic
    >
new MCTS
    ≈
old MCTS
    >
Alpha-Beta
    >
Random
```

This ordering is specific to the tested implementations, parameters, checkpoints, and match configuration.

It should not be interpreted as a general theoretical ranking of the algorithms.

---

## Files and Dependencies

| File or directory | Role |
|---|---|
| `bots.py` | Agent implementations |
| `run_experiment.py` | Pairwise bot evaluation |
| `play_tournament.py` | Multi-agent tournament execution |
| `human_vs_bot.py` | Manual agent evaluation |
| `EvalFunction/` | Neural checkpoints |
| `EvaluationFunction/logix_az/` | Environment and network dependencies |

---

## Testing Agents

Useful agent tests include:

- selected move is always legal,
- original environment remains unchanged during search,
- immediate winning moves are selected,
- no-move states are handled safely,
- fixed seeds produce repeatable results,
- neural checkpoints load successfully,
- policy cache keys are hashable,
- search respects configured limits.

For search-based agents, small constructed positions are often more useful than full games because the expected best move can be verified manually.

---

## Related Documentation

- [Bot Experiments Overview](overview.md)
- [Tournament Framework](tournament-framework.md)
- [Results](results.md)
- [Game Environment](../evaluation-function/environment.md)
- [Neural Network](../evaluation-function/neural-network.md)
- [MCTS and Self-Play](../evaluation-function/mcts-and-self-play.md)
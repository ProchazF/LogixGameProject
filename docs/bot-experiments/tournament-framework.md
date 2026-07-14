# Tournament Framework

[← Back to BotExperiments](../../BotExperiments/README.md)

## Overview

The tournament framework automates large-scale evaluation of Logix agents.

It provides a common execution environment where different bots can compete under identical conditions while recording detailed statistics for later analysis.

The main tournament logic is implemented in:

```text
play_tournament.py
```

while individual experiments can be executed using:

```text
run_experiment.py
```

---

## Tournament Workflow

Every tournament follows the same sequence.

```text
Select Agents
      │
      ▼
Create Match Schedule
      │
      ▼
Initialize Environment
      │
      ▼
Play Games
      │
      ▼
Save Results
      │
      ▼
Generate Statistics
```

Each match is completely independent of previous games.

---

## Match Execution

For every game the framework performs the following steps:

1. Create a new `LogixShapeEnv`.
2. Initialize both agents.
3. Alternate turns until the game ends.
4. Record match statistics.
5. Save the completed match.

The environment is reset before every game to ensure identical starting conditions.

---

## Agent Interface

Every bot is expected to implement the same interface.

Conceptually:

```python
move = bot.choose_move(environment)
```

The returned move must be one of:

```python
environment.legal_moves()
```

This common interface allows different search algorithms to participate in the same tournament without modifying the tournament framework.

---

## Player Order

To reduce first-player bias, tournaments alternate player positions.

For example:

```text
Game 1

Player A
vs
Player B

Game 2

Player B
vs
Player A
```

This produces a more reliable estimate of relative playing strength.

---

## Tournament Types

The framework supports several evaluation scenarios.

### Head-to-Head

A fixed pair of agents plays many games.

Typical uses include:

- parameter tuning,
- checkpoint comparison,
- algorithm benchmarking.

---

### Round-Robin

Every agent plays against every other agent.

This produces a complete comparison table between all implemented bots.

---

### Human Evaluation

Human games can also be played against implemented agents using:

```text
human_vs_bot.py
```

Although these games are not part of automated tournaments, they provide useful qualitative evaluation.

---

## Statistics

For every completed game, the framework records information such as:

- participating agents,
- winner,
- game result,
- number of moves,
- execution time.

These records are later aggregated into tournament summaries.

---

## Saving Progress

Large tournaments may require many hours to complete.

To prevent data loss, progress is saved **after every completed match**.

Saved information includes:

- completed games,
- accumulated statistics,
- tournament configuration.

If execution is interrupted, the tournament can continue without replaying finished games.

---

## Resume Support

When an existing tournament directory is detected, execution can continue from the latest saved state.

Only unfinished matches are scheduled.

This makes it practical to evaluate large tournaments over multiple sessions.

---

## Output Files

Tournament results are written to the `results/` directory.

A typical tournament contains:

```text
config.json
games.csv
summary.json
```

Additional visualizations such as win-rate heatmaps and score plots may also be generated automatically.

---

## Fair Evaluation

To ensure reproducible and comparable results, every match uses:

- identical game rules,
- the same board size,
- the same maximum game length,
- identical environment implementation.

Only the decision-making algorithm differs between participating agents.

---

## Performance

The total running time depends primarily on:

- number of games,
- number of participating agents,
- search complexity,
- neural-network inference time.

Simple agents such as `RandomBot` finish almost instantly, while search-based agents may require substantially longer per move.

---

## Extension

Adding a new tournament format generally requires only:

1. defining the match schedule,
2. creating the participating agents,
3. executing the standard match runner,
4. recording the resulting statistics.

Since all agents share the same interface, no changes to the game loop are typically required.

---

## Related Documentation

- [Overview](overview.md)
- [Implemented Agents](implemented-agents.md)
- [Results](results.md)
- [Evaluation Function](../evaluation-function/overview.md)
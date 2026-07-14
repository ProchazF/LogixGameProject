# Bot Experiments Overview

[← Back to BotExperiments](../../BotExperiments/README.md)

## Purpose

The **BotExperiments** module provides a common framework for evaluating and comparing all implemented Logix agents under identical conditions.

Instead of focusing on training or gameplay, this module automates large-scale tournaments, records detailed match statistics, and generates visual summaries of the results.

It serves as the primary evaluation environment for measuring the playing strength of different search algorithms and neural-network checkpoints.

---

## Architecture

The experimental framework consists of four main components:

```text
Implemented Agents
        │
        ▼
Match Runner
        │
        ▼
Tournament Manager
        │
        ▼
Result Analysis
```

Each component is independent, allowing new agents or tournament formats to be added without modifying the remaining framework.

---

## Project Structure

| File / Directory | Responsibility |
|------------------|----------------|
| `bots.py` | Implements all available agents. |
| `run_experiment.py` | Executes individual head-to-head experiments. |
| `play_tournament.py` | Runs complete round-robin tournaments. |
| `human_vs_bot.py` | Allows manual games against implemented agents. |
| `concatenate_results.py` | Combines statistics from multiple experiment runs. |
| `results/` | Stores experiment outputs, statistics, and plots. |
| `EvalFunction/` | Contains neural-network checkpoints used by neural agents. |

---

## Experimental Workflow

A typical experiment follows these steps:

```text
Create Agents
      │
      ▼
Initialize Environment
      │
      ▼
Play Match
      │
      ▼
Record Statistics
      │
      ▼
Repeat for All Games
      │
      ▼
Generate Summary
```

Each game is played using the same Logix environment, ensuring that all agents compete under identical game rules.

---

## Match Execution

For every game the framework:

1. Creates a new game environment.
2. Initializes both participating agents.
3. Alternates turns until the game ends.
4. Records the winner, move count, and execution time.
5. Stores the complete result.

Player order is alternated during tournaments to reduce first-player advantage.

---

## Tournament Types

The framework supports several evaluation scenarios.

### Head-to-Head Matches

Two selected agents repeatedly play against one another.

These experiments are useful for:

- comparing algorithm variants,
- evaluating neural checkpoints,
- testing parameter changes.

### Full Tournaments

Every implemented agent plays against every other agent.

Tournament summaries include:

- win rates,
- total scores,
- average game length,
- execution times.

### Human vs Bot

The framework can also be used to manually evaluate agent behaviour by allowing a human player to compete against any implemented bot.

---

## Recorded Statistics

Each completed game produces information such as:

- winner,
- game result,
- move count,
- execution time,
- participating agents.

Tournament summaries aggregate these values to compute overall performance metrics.

---

## Output

Experiment results are stored inside the `results/` directory.

Typical outputs include:

- CSV files containing per-game statistics,
- JSON summaries,
- tournament configuration files,
- performance plots,
- win-rate heatmaps.

These outputs can be reused for later analysis without replaying the games.

---

## Resume Support

Long-running tournaments support checkpointing.

After each completed match, the current results are written to disk.

If execution is interrupted, the tournament can continue from the latest saved state instead of restarting from the beginning.

This greatly reduces the cost of evaluating large numbers of games.

---

## Relationship to Other Modules

The experiment framework depends on two other project components.

### EvaluationFunction

Provides:

- the Logix environment,
- trained neural-network checkpoints,
- state representation.

### LogixGame

Provides the playable Unity implementation but is not required for automated experiments.

All experiments are executed entirely within the Python framework.

---

## Extension

Adding a new agent typically requires only:

1. Implementing the bot in `bots.py`.
2. Providing a `choose_move()` method.
3. Registering the bot inside the experiment script.

Once registered, the new agent can participate in all supported tournament formats without additional changes.

---

## Related Documentation

- [Tournament Framework](tournament-framework.md)
- [Implemented Agents](implemented-agents.md)
- [Results](results.md)
- [Evaluation Function](../evaluation-function/overview.md)
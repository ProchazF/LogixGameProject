# Results

[← Back to BotExperiments](../../BotExperiments/README.md)

## Overview

The experiment framework records detailed information about every completed match and automatically generates summary statistics for the entire tournament.

All results are stored inside the `results/` directory, allowing experiments to be inspected, resumed, or compared without replaying games.

---

## Directory Structure

A typical tournament directory contains:

```text
results/
│
└── tournament_name/
    ├── config.json
    ├── games.csv
    ├── summary.json
    ├── avg_moves.png
    ├── total_scores.png
    └── winrate_heatmap.png
```

Additional files may be generated depending on the experiment configuration.

---

## Configuration

Each experiment stores its configuration in:

```text
config.json
```

Typical information includes:

- participating agents,
- number of games,
- tournament settings,
- search parameters,
- random seeds,
- checkpoint versions.

Saving the configuration makes experiments reproducible.

---

## Per-Game Results

Every completed match is recorded in:

```text
games.csv
```

Each row typically contains:

- player A,
- player B,
- winner,
- result,
- number of moves,
- game duration.

This file allows individual games to be inspected or processed using external tools.

---

## Tournament Summary

Overall tournament statistics are stored in:

```text
summary.json
```

Typical values include:

- total wins,
- losses,
- draws,
- win rates,
- total scores,
- average game length,
- average move time.

The summary provides a compact overview of agent performance.

---

## Visualizations

The framework automatically generates several plots.

Typical visualizations include:

- win-rate heatmap,
- total score chart,
- average game length,
- average move time.

These figures provide a quick overview of tournament results without inspecting raw data.

---

## Combined Statistics

Results from multiple tournaments can be merged using:

```text
concatenate_results.py
```

The combined output is written to:

```text
results/combined_statistics/
```

This allows experiments performed on different days or with different configurations to be analysed together.

---

## Resume Support

Tournament progress is saved after every completed match.

If execution is interrupted, existing result files are loaded and only unfinished matches are played.

This prevents previously completed games from being repeated.

---

## Interpreting Results

Agent strength should be evaluated using multiple metrics rather than a single win rate.

Useful indicators include:

- overall win rate,
- head-to-head performance,
- average game length,
- average move time,
- tournament score.

Large numbers of games generally provide more reliable estimates than small samples.

---

## Reproducibility

When comparing experiments, the following should remain consistent:

- game rules,
- tournament format,
- search parameters,
- checkpoint versions,
- random seeds (when applicable).

Differences in any of these settings may influence the observed results.

---

## Related Documentation

- [Overview](overview.md)
- [Tournament Framework](tournament-framework.md)
- [Implemented Agents](implemented-agents.md)
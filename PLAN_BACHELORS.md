# Logix Game AI Extension Plan

## Project Overview
This phase extends the existing Logix game project by improving the **AI bots** and developing a **neural network–based evaluation function** to guide Monte Carlo Tree Search (MCTS).

The base game and simple bots (random, heuristic, and basic MCTS) are already implemented.  
The new goal is to advance AI decision-making through better search strategies, heuristics, and machine learning–based evaluation.

---

## Goals
- Upgrade existing bots for stronger, more stable play.
- Integrate **PUCT-based MCTS** with better rollout and expansion logic.
- Design and train a **neural network evaluation function** for game state scoring.
- Build a framework for **self-play data generation, training, and integration**.
- Enable reproducible **experiments and Elo-based comparisons**.

---

## Milestone A — Bot Improvements

### A1. MCTS Enhancements
- Still working subotimally, in terms of time consumed and move selection

### A2. Heuristic Bot 2.0
- Better the bots owith some heuristics

### A3. Arena & Elo System
- Implement a better Bot v Bot gamemode, one without visuals, just a fast playout

---

## Milestone B — Neural Network Evaluation Function

### B1. State Representation
- Encode board as a **multi-channel tensor (C × 7 × 7)**:
- Channels: player colors, black (mandatory in shapes), grey (joker), last-move mask.
- Add scalar meta-features (turn number, player inventory).
- Data augmentation: 4 rotations (no mirroring, as reflections are unique shapes).

### B2. Dataset Creation
Two data paths:
1. **Imitation from Search (AlphaZero-style)**  
 - Use strong MCTS to generate (state, π, z) tuples:
   - `π`: visit count distribution  
   - `z`: final outcome (+1, 0, -1)
2. **Value-only Supervised Training**  
 - From self-play games, store (state, value target).


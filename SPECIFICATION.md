# Logix Game – Semester Project Specification

## Overview

The project aims to design and implement a **digital version of the board game *Logix***, complete with a user-friendly interface, support for multiple game modes, and an AI-controlled bot opponent. The game will be developed using the **Unity game engine** in C#.  

**Key goals:**
- Digitize the *Logix* game with polished UI
- Support both human and AI opponents
- Enable multiple play modes (PvP, PvE, Bot vs Bot)
- Develop an AI bot using search algorithms (e.g., Alpha-Beta, MCTS)
- Document the rules, design, and implementation

---

## Features

### Core Gameplay
- Turn-based, logic-based board game
- Rule enforcement and legal move validation
- Win condition detection
- Game state management (board, turn info)

### Game Modes
- Player vs Player (local)
- Player vs Bot
- Bot vs Bot (spectator mode)

### AI Bot
- Modular bot interface
- Algorithmic decision-making (e.g., Alpha-Beta pruning or MCTS)
- Difficulty scaling (adjustable depth/time limits)

### User Interface
- Main menu with mode selection
- Interactive game board
- Game status display (turn indicator, winner notification)
- Restart/exit options

### Spectator Features
- Bot vs Bot mode with live updates

---

## Optional / Stretch Features - possivly for Bachelor's
- Online multiplayer using Unity Netcode
- Advanced bot difficulty levels
- Adaptive AI that learns from player behavior
- Reinforcement Learning-based agent

---

## Deliverables

- **Playable Logix game** (Unity project)
- **AI bot** capable of playing competently
- **Polished UI and UX**
- **Fully implemented game modes**: PvP, PvE, Bot-vs-Bot
- **Codebase** with documentation
- **Project presentation/demo-ready build**

---

## Tools & Technologies

- **Engine**: Unity
- **Language**: C#
- **Version Control**: Git (GitHub or GitLab)
- **Testing**: Unity Test Runner
- **Planning/Documentation**: Markdown files
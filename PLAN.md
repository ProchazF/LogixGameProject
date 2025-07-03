 Logix Game Semestral Project Plan

## Project Overview
This project involves developing a digital version of the logic-based board game **Logix**, complete with a user interface and support for different gameplay modes. The game will support:

- Player vs Player (local)
- Player vs Bot
- Bot vs Bot (spectator mode)

The project also includes the development of a bot capable of playing Logix using algorithmic reasoning and decision-making. Additional PvP modes with custom rules or constraints will also be explored.

The game will be developed using the **Unity** game engine, which may require an initial learning phase.

---

## Stage 1: Unity Onboarding & Game Design
**Timeline:** Next consultation (from the first one focused on project)

- Get familiar with Unity Editor, GameObjects, Scenes etc.
- Follow Unity tutorials related to board games and turn-based logic
- Define and document the rules of Logix (win condition, legal moves, board state, etc.)
- Identify required game components (e.g., board representation, player turns, input methods)
- Create wireframes or mockups using Unity's UI system
- Plan architecture (e.g., MVC, ScriptableObjects)

---

## Stage 2: Game Core Logic & Data Structures
**Timeline:** 2nd consultation

- Implement board data structure and core game logic (rules engine) in C#
- Add move validation and state updates
- Define player types (human, bot placeholder)
- Implement win condition checking
- Write C# unit tests using Unity Test Framework

---

## Stage 3: Game UI & Scene Management
**Timeline:** 3rd consultation

- Set up the main scene and game board using prefabs and Grid layout
- Implement interactivity: highlighting legal moves, handling user input
- Display game status (turn info, winner, etc.)
- Add UI menus: mode selection, restart, exit
- Polish user experience with Unity animations or transitions

---

## Stage 4: Bot Development
**Timeline:** 4th consultation

- Define bot API and interface with game logic
- Implement a bot using alpha-beta pruning/MCTS
- Support difficulty levels or adjustable depth/time?
- Test bot against different scenarios

---

## Stage 5: Game Modes & Spectator Features
**Timeline:** 5th consultation

- Implement Player vs Bot and Bot vs Bot modes
- Add ability to spectate bot matches with live visual updates
- Finalize Player vs Player mode with possible rule variations (timers, score modes)?

---

## Stage 6: Polish, QA & Packaging
**Timeline:** 6th consultation

- Bug fixing, UI/UX improvements, and animations
- Final pass on all game modes
- Document code and usage
- Prepare for project presentation/demo

---

## Optional Features (Time Permitting)
- Online multiplayer using Unity Netcode
- Multiple bot difficulty settings

---

## Deliverables
- Playable Logix game in Unity
- AI bot that can play the game with reasonable competence
- Polished UI and usability
- Game modes: PvP, PvE, Bot-vs-Bot
- Code + documentation

---

## Tools & Technologies
- Engine: Unity
- Language: C#
- Version control: Git (GitHub or GitLab)
- Testing: Unity Test Runner
- Planning: This markdown file

---
## Bachelor's Thesis Ideas (AI Major)
- **Search Algorithms in Board Game AI:** Explore and compare different algorithms (e.g., Minimax, Alpha-Beta, MCTS) applied to Logix.
- **AI Difficulty Adaptation:** Implement and study an adaptive bot that changes behavior based on opponent skill - this one could be good for probabilistic aproach
- **Reinforcement Learning Agent for Logix:** Train an agent using RL and analyze learning curve and performance- this sounds fun
- **Human-AI Interaction in Turn-Based Games:** Study usability, challenge, and engagement in mixed-mode matches.
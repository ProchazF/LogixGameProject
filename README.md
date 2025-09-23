# Logix

Logix is a strategic board game implemented in Unity.  
Players compete by placing, moving, and replacing marbles on a 7×7 board, aiming to form specific 5-marble winning shapes (Pentominos).  

This project was created as part of a university coursework in game development and artificial intelligence.

---

## Features

- 7×7 interactive board with drag-and-drop marble placement.
- Multiple game modes:
  - **PvP**: Player vs Player (local multiplayer).
  - **PvE**: Player vs AI (bot with adjustable difficulty).
  - **EvE**: Bot vs Bot (AI vs AI).
- AI powered by **Monte Carlo Tree Search (MCTS)**.
- Color restrictions: cannot reuse opponent’s last color(s).
- Inventory system with limited marbles (including grey jokers).
- Shape cards: each player has two shapes that determine their win condition.
- Rules and About panels included in the main menu.
- UI built with Unity’s Canvas + TextMeshPro.

---

## Download & Installation

### Windows
1. Download the latest release:  
   [Logix_Windows.zip] in /Builds/Logix_Windows.zip
2. Extract the `.zip` file anywhere.  
3. Run `Logix.exe` to start the game.  
4. No installation required.

---

## How to Play

- The board starts with a **black marble** in the center.
- Players take turns. On your turn, you may:
  - Place a marble from shared inventory **orthogonally adjacent** to an existing marble.
  - Move a marble on the board to an empty adjacent valid spot (if not blocked).
  - Replace an opponent’s marble with one from inventory.
- Restrictions:
  - You **cannot use the same color(s)** your opponent used in their last move.
  - Grey marbles = jokers (wildcards, count as any color).
  - Black marble must always be part of a winning shape.
- Winning condition:
  - Form a **five-marble shape** that matches one of your two shape cards.
  - Shapes may be rotated, but **not mirrored**.
  - The shape must be made from **one consistent color** (except black/grey).
  - The card’s **blocked color** cannot be used.
  - The winning shape must be **exactly five connected marbles of the same color**, meaning no extra marbles of that color may be connected to the shape (grey is fine)

---

## Controls

- **Click marble in inventory** → select it.  
- **Click board tile** → place or move marble.  
- **Click opponent marble** → replace it (if legal).  
- **Back button** (Rules/About) → return to menu.  
- **Main Menu button** (GameScene) → exit to menu.  

---

## AI

- AI difficulty is adjustable:
  - **Easy** → random playout (fast, weaker).  
  - **Normal** → ~500 simulations (balanced).  
  - **Hard** → ~2000 simulations (stronger, slower).  
- AI uses **Monte Carlo Tree Search (MCTS)** with random simulations and immediate win detection.

---

## Development Info

- **Engine**: Unity 6 (6000.x)  
- **Language**: C# 
- **UI**: Unity Canvas + TextMeshPro 
- **AI**: Monte Carlo Tree Search

### Project Structure
- **Core Components**: GameManager, GameBoard, Move, WinShape, etc.  
- **AI Components**: BotController, MCTSBot.  
- **UI Components**: BoardVisualizer, InventoryUI, CardUI, CursorMarble, etc.  

---

## License / Credits

- Developed by *František Procházka*.  
- University coursework project.  
- Free to use for educational or entertainment purposes.  

---

## Screenshots



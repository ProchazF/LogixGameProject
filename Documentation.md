# Logix – Project Documentation

## 1. Introduction
Logix is a strategy board game implemented in Unity.  
Players take turns placing, moving, or replacing marbles on a 7×7 grid, with the goal of forming specific 5-marble shapes called *winning cards*.  

This document describes the rules, architecture, user interface, and AI implementation of the game.

---

## 2. Game Rules

### 2.1 Board and Setup
- Board size: **7×7 grid**  
- Initial setup: **one black marble in the center**  
- Each player’s inventory:  
  - 6 × Red, 6 × Blue, 6 × Green, 6 × Yellow  
  - 2 × Grey (joker marbles)  
- Each player receives **2 winning cards**, each linked to a *shape* and a *blocked color*.

### 2.2 Player Actions
On their turn, a player may:  
1. **Place** a marble from inventory (must be orthogonally adjacent to another marble).  
2. **Move** an existing marble (if it is not blocked).  
3. **Replace** an opponent’s marble with one from inventory.  

### 2.3 Restrictions
- A player **cannot use the same color(s)** used by their opponent in the previous move.  
- Grey marbles act as jokers (wildcards).  
- Black marble must always be part of a winning shape.  

### 2.4 Winning Condition
- First player to form one of their winning cards’ shapes wins.  
- Shape must:  
  - Use **5 connected marbles** (including black).  
  - Match rotation of the card (mirroring not allowed).  
  - Be built from a single color (with grey/black allowed).  
  - Not use the card’s **blocked color**.  

---

## 3. Core Components (Scripts)

This section describes the main scripts that form the backbone of Logix.  
Each script is responsible for a different layer of the game: rules, state management, and user interface.

### 3.1 GameManager

**Role:**  
The central controller of the game. Handles initialization, player turns, input validation, invoking AI, win checking, and UI updates.

**Key Responsibilities:**
- Initializes the game board (`GameBoard`) and visualizer (`BoardVisualizer`).  
- Assigns winning cards to both players while preventing duplicates.  
- Manages turns
- Connects player input and bot AI.  
- Detects win conditions and displays victory UI.  
- Provides methods for handling inventory selections, tile clicks, and rollback logic.

**Important Fields:**
- `GameMode mode` – PvP, PvE, or EvE.  
- `Difficulty botA, botB` – difficulty settings for AI bots.  
- `GameBoard myBoard` – internal logic board.  
- `BoardVisualizer boardVisualizer` – visual representation of the board.  
- `InventoryUI inventoryUI` – handles inventory display.  
- `IllegalMarblesUI illegalMarblesUI` – shows restricted marbles.  
- `WinShapeInstance[] playerACards, playerBCards` – each player’s winning cards.  
- `int currentPlayer` – 0 = Player A, 1 = Player B.  

**Important Methods:**
- `Start()` – sets up the game board, assigns cards, initializes UI.  
- `Awake()` – reads PlayerPrefs for mode and difficulty, spawns bots if needed.  
- `OnMarbleSelected(MarbleColor color)` – handles inventory selection.  
- `OnTileClicked(int x, int y)` – handles clicks on board tiles (place, move, replace).  
- `AfterMoveSuccess(MarbleColor usedColor)` – updates state after a valid move, switches turn, and triggers bot if needed.  
- `CheckForWin()` – checks if either player has completed a winning shape.  
- `ShowWin(string playerName, string shapeName, List<Vector2Int> positions)` – displays victory screen.  
- `RollbackToOriginal()` – restores marble if move was invalid.  

**Notes:**
- `GameManager` enforces the rule “cannot use the same color as previous move” via `previousMoveColors`.  
- Also responsible for sequencing bot turns (`DoBotTurn` coroutine).

---
### 3.2 GameBoard

**Role:**  
Encapsulates all **game rules and state management**. This is the “true” game logic independent of UI.

**Key Responsibilities:**
- Stores the board grid (7×7).  
- Manages marble placement, movement, and replacement.  
- Tracks inventory of available marbles.  
- Validates moves against rules (adjacency, blocked moves, illegal colors).  
- Provides legal move generation (`GetLegalMoves()`).  
- Checks for winning conditions (`CheckWinFromBlack`).  

**Important Fields:**
- `int width, height` – board dimensions.  
- `MarbleColor[,] grid` – board state (empty, red, blue, green, yellow, grey, black).  
- `Dictionary<MarbleColor, int> inventory` – player inventories.  
- `HashSet<MarbleColor> previousMoveColors` – restricted colors from last move.  

**Important Methods:**
- `PlaceMarble(int x, int y, MarbleColor color)` – places marble from inventory.  
- `MoveMarble(int fromX, int fromY, int toX, int toY)` – moves existing marble.  
- `ReplaceMarble(int x, int y, MarbleColor newColor)` – replaces existing marble.  
- `PickUpMarble(int x, int y, out MarbleColor pickedColor)` – used for move selection.  
- `CanMoveTo(int fromX, int fromY, int toX, int toY)` – checks if a marble can move.  
- `GetLegalMoves()` – generates all possible legal moves for current player.  
- `CheckWinFromBlack(WinShapeInstance[] cards, out WinShape matched, out List<Vector2Int> positions)` – checks if any winning card shape is satisfied.  
- `Clone()` – deep copy for AI simulations.  

**Notes:**
- Independent of Unity UI – this makes it suitable for testing and AI.  
- All rule enforcement happens here (adjacency, blocked colors, etc.).

---
### 3.3 BoardVisualizer

**Role:**  
Handles the **visual representation** of the `GameBoard` state.  
It doesn’t enforce rules – it only reflects the current state and sends user input back to `GameManager`.

**Key Responsibilities:**
- Generates the 7×7 tile grid in Unity.  
- Updates marble sprites/colors based on board state.  
- Highlights winning shapes when game ends.  
- Handles tile clicks and routes them to `GameManager`.

**Important Fields:**
- `GameBoard board` – reference to logic board.  
- `Action<int, int> onTileClickedCallback` – callback for tile clicks.  

**Important Methods:**
- `Init(GameBoard board)` – initializes tiles.  
- `Refresh()` – redraws the board to match the `GameBoard`.  
- `HighlightWin(List<Vector2Int> positions)` – visually highlights winning marbles.  

**Notes:**
- Keeps UI and game logic decoupled.  
- Can easily be replaced with another visualization layer (e.g., 3D board).

---
### 3.4 InventoryUI

**Role:**  
Displays and manages the player’s available marbles.

**Key Responsibilities:**
- Shows counts for each marble color.  
- Updates counts after each placement/replacement.  
- Lets players click to select a marble color.  

**Important Methods:**
- `Init(Dictionary<MarbleColor, int> inventory)` – initializes counts from GameBoard.  
- `UpdateCount(MarbleColor color, int count)` – updates displayed count.  

--- 
### 3.5 IllegalMarblesUI

**Role:**  
Displays marbles/colors that are **illegal to play** in the current turn.

**Key Responsibilities:**
- Updates the list of restricted colors after each move.  
- Provides clear visual feedback to the player.  

**Important Methods:**
- `SetIllegalMarbles(HashSet<MarbleColor> colors)` – highlights illegal marbles.  

--- 
### 3.6 CardUI

**Role:**  
Handles the **visual display of winning cards** assigned to players.

**Key Responsibilities:**
- Displays the shape name and blocked color.  
- Allows easy reference during gameplay.  

**Important Methods:**
- `Init(WinShapeInstance card)` – initializes card display.  
- Can show both text (shape name) and an image/icon (shape preview).

---

## Summary of Core Components

- **GameManager** = Orchestrator (brains of the game flow).  
- **GameBoard** = Rules & logic (independent, testable).  
- **BoardVisualizer** = Rendering (UI for the board).  
- **InventoryUI** = Marble inventory display & selection.  
- **IllegalMarblesUI** = Shows banned colors.  
- **CardUI** = Displays player’s winning cards.  

By keeping these concerns separate, the game logic remains **testable** and **extendable**, while UI elements stay focused only on presentation and interaction.

---

### 3.2 AI Components
- **BotController** – interface between GameManager and AI.  
- **MCTSBot** – implements Monte Carlo Tree Search for decision-making.  

### 3.3 Data Flow
- UI input → GameManager → GameBoard (logic update) → BoardVisualizer (render update).  
- For AI turns: GameManager → BotController → MCTSBot → returns `Move`.

---

## 4. AI Components

The AI system in Logix is built around a **BotController** that manages interaction between the `GameManager` and a search-based decision-making algorithm (`MCTSBot`).  
This separation allows easy replacement of the AI algorithm (e.g., heuristics, minimax) while keeping the rest of the game unchanged.

---

### 4.1 BotController

**Role:**  
Provides a unified interface for AI players. The `GameManager` calls into `BotController` to obtain a move whenever it is a bot’s turn.

**Key Responsibilities:**
- Store the bot’s difficulty level.  
- Instantiate and manage the search algorithm (`MCTSBot`).  
- Return the best move for the bot given the current game state.  
- Allow easy extension to support other AI types in the future.  

**Important Fields:**
- `Difficulty difficulty` – Easy / Normal / Hard.  
- `MCTSBot mctsBot` – the algorithm instance.  

**Important Methods:**
- `SetDifficulty(Difficulty diff)` – assigns the difficulty and configures iteration count for MCTS.  
- `Move GetMove(GameBoard board, WinShapeInstance[] playerACards, WinShapeInstance[] playerBCards, int currentPlayer)`  
  - Clones the current game state.  
  - Runs the AI algorithm with the selected difficulty.  
  - Returns the chosen move to the GameManager.  

**Notes:**
- In PvE, only Player B uses `BotController`.  
- In EvE, both Player A and Player B use separate `BotController` instances with independent difficulties.  
- `GameManager` does not need to know about MCTS details — it only interacts with `BotController`.

---

### 4.2 MCTSBot

**Role:**  
Implements **Monte Carlo Tree Search (MCTS)** to evaluate moves by running many randomized simulations from the current state.  
This gives the bot a balance between tactical strength and unpredictability.

**Key Responsibilities:**
- Search game tree by iteratively exploring moves.  
- Apply the four phases of MCTS (Selection, Expansion, Simulation, Backpropagation).  
- Detect immediate wins (shortcut instead of random rollout).  
- Respect game rules (illegal colors, adjacency, black marble requirement).  
- Choose the most promising move after a fixed number of iterations.

**Important Fields:**
- `int iterations` – number of rollouts per move (higher = stronger AI).  
- `Node` (inner class) – tree structure representing states and moves.  

**Node Structure:**
- `GameBoard State` – snapshot of the board at this node.  
- `Move Move` – move that led to this state.  
- `Node Parent` – reference to parent node.  
- `List<Node> Children` – expanded moves.  
- `int Visits` – number of times visited.  
- `float Wins` – accumulated score for root player.  
- `int PlayerToMove` – whose turn it is at this node.

---

### 4.3 MCTS Algorithm in Logix

**1. Selection**  
- Start from the root node (current board).  
- Repeatedly select the child with the **highest UCT score** until reaching a leaf or a not-fully-expanded node.  

UCT Formula:
- `C` is exploration constant (commonly √2).  
- Balances exploitation (good moves) and exploration (new moves).  

**2. Expansion**  
- Generate legal moves from the selected node.  
- If an unexpanded move exists:  
  - Clone board, apply the move, create a new node.  
  - Immediate win moves are prioritized.  

**3. Simulation (Rollout)**  
- From the new node, simulate random moves until:  
  - A win condition is found, or  
  - A depth/safety limit is reached (e.g., 50 plies).  
- Return result as:  
  - `1.0` if root player eventually wins.  
  - `0.0` if opponent wins.  
  - `0.5` if no outcome (draw/undecided).  

**4. Backpropagation**  
- Traverse back up to the root.  
- Increment visits at each node.  
- Add result to wins (always from **root player perspective**).  

---

### 4.4 Difficulty Settings

The difficulty level directly affects the number of iterations performed:  

| Difficulty | Iterations (approx.) | Behavior |
|------------|----------------------|----------|
| Easy       | ~100                 | Quick but weak, often random-like. |
| Normal     | ~500                 | Balanced strength and speed. |
| Hard       | ~2000                | Strong, calculates deeper, but slower. |

- In PvE, Player B uses BotA’s difficulty (per project spec).  
- In EvE, both bots use their assigned difficulty levels independently.  

---

### 4.5 Strengths and Limitations

**Strengths:**
- General approach, works without handcrafted heuristics.  
- Finds immediate winning moves reliably.  
- Difficulty is easily adjustable.  

**Limitations:**
- Rollouts are random → sometimes weak positional play.  
- Computationally expensive at high iterations.  
- Without heuristics, may still prefer shallow strategies.  

---

### 4.6 Future Improvements
- Add **heuristic evaluation** to rollouts (not just random).  
- Add **transposition table** to reuse states.  
- Parallelize simulations for faster results.  
- Hybrid approach: MCTS + rule-based pruning.  
- Smarter immediate-loss prevention (block opponent’s win).  

---

## Summary of AI Components

- **BotController** – bridge between GameManager and AI.  
- **MCTSBot** – performs the actual search.  
- **Node** – tree data structure.  
- MCTS phases (Selection, Expansion, Simulation, Backpropagation) implemented specifically for Logix rules.  
- Difficulty scaling by iteration count.  

This modular design allows easy replacement of the AI algorithm in the future (e.g., a minimax bot or heuristic bot), without changing the rest of the game.

---

## 5. User Interface

The Logix user interface is built around two main scenes:

- **Main Menu (SampleScene)** – entry point of the game, where the player selects mode, difficulty, and can read Rules/About.  
- **Game Scene (GameScene)** – where the board is displayed and gameplay happens.  

All UI is built using Unity’s **Canvas system** with TextMeshPro for text rendering.

---

### 5.1 Main Menu (SampleScene)

**Panels:**
- **MainMenuPanel**  
  - Buttons:  
    - **Play** → opens mode selection.  
    - **Rules** → shows RulesPanel.  
    - **About** → shows AboutPanel.  
    - **Quit** → exits the application.  
  - This panel is the default visible one.  

- **ModeSelectionPanel**  
  - Buttons:  
    - **PvP** → starts Player vs Player game.  
    - **PvE** → opens DifficultyPanel.  
    - **EvE** → opens BotVsBotPanel.  

- **DifficultyPanel** (for PvE)  
  - Buttons: Easy / Normal / Hard.  
  - Starts a PvE game with selected difficulty.  

- **BotVsBotPanel** (for EvE)  
  - Two sets of difficulty buttons (for Bot A and Bot B).  
  - Button **Start** → launches EvE match with chosen difficulties.  

- **RulesPanel**  
  - Contains a **Scroll View** with a TextMeshPro text component.  
  - Displays the rules of Logix.  
  - Includes a **Back button** to return to MainMenuPanel.  

- **AboutPanel**  
  - Contains a **Scroll View** with text explaining the game’s purpose and credits.  
  - Includes a **Back button** to return to MainMenuPanel.  

**Navigation Flow:**
- **MainMenuPanel → ModeSelectionPanel → DifficultyPanel/BotVsBotPanel → GameScene**  
- **MainMenuPanel → RulesPanel → Back → MainMenuPanel**  
- **MainMenuPanel → AboutPanel → Back → MainMenuPanel**  

**Implementation Details:**
- Panels are toggled via `MainMenuManager.cs`.  
- PlayerPrefs are used to save mode/difficulty choices so `GameManager` can read them in `GameScene`.  
- Quit button only visible in MainMenuPanel (hidden in sub-panels).  

---

### 5.2 Game Scene (GameScene)

**Main Elements:**
- **BoardVisualizer**  
  - Displays the 7×7 grid of tiles.  
  - Each tile shows either empty or a marble.  
  - Handles highlighting (win shapes).  
  - Detects mouse clicks and sends them to `GameManager.OnTileClicked(x, y)`.  

- **InventoryUI**  
  - Shows remaining marbles for current player (Red, Blue, Green, Yellow, Grey).  
  - Each marble is clickable → triggers `GameManager.OnMarbleSelected(color)`.  
  - Count updates after placement/replacement.  

- **IllegalMarblesUI**  
  - Displays marbles/colors that are **illegal this turn** (the colors used by opponent in their last move).  
  - Helps player avoid invalid selection.  

- **Player Cards (CardUI)**  
  - Each player has two cards.  
  - Card shows:  
    - Shape name.  
    - Blocked color (the forbidden color for that card).  
  - Displayed at top (Player B) and bottom (Player A) of the screen.  

- **CursorMarble**  
  - A floating marble graphic following the mouse when a marble is selected.  
  - Clears after move is made or cancelled.  

- **Turn Text (TextMeshProUGUI)**  
  - Shows whose turn it is (Player 1, Player 2, Bot A, Bot B, etc.).  
  - Updates every turn switch.  

- **Win Panel**  
  - Hidden until a win condition is met.  
  - Displays:  
    - Winner name.  
    - Shape name that caused win.  
  - Buttons: **Return to Main Menu**.  

---

### 5.3 Input Flow

**Inventory → Placement**
1. Player clicks on a marble in `InventoryUI`.  
   - `GameManager.OnMarbleSelected()` sets selected color.  
   - `CursorMarble` shows the marble under cursor.  
2. Player clicks a valid empty tile in `BoardVisualizer`.  
   - `GameManager.OnTileClicked()` validates move using `GameBoard`.  
   - If valid, marble is placed, inventory updated.  
   - If invalid, move is rejected and selection reset.  

**Move from Board**
1. Player clicks a marble already on board.  
   - `PickUpMarble` in `GameBoard` checks if movable.  
   - If yes, marble is removed temporarily, cursor follows.  
2. Player clicks target tile.  
   - `CanMoveTo()` checks legality.  
   - If valid, marble is moved.  
   - If not valid, marble is restored to original position.  

**Replacement**
1. Player selects a marble from inventory.  
2. Clicks on a tile occupied by opponent’s marble (not black).  
3. If replacement allowed, marble is swapped and inventory updated.  

---

### 5.4 Bot Turns

- When it is a bot’s turn:  
  - `GameManager` calls `StartCoroutine(DoBotTurn(bot))`.  
  - Bot displays "Bot is thinking…" in turn text.  
  - After thinking delay, bot chooses move via `BotController`.  
  - Move applied by `GameManager.ApplyBotMove()`.  
  - Visuals updated (`BoardVisualizer.Refresh()`).  

---

### 5.5 Design Notes

- All UI is separated into **logic vs visuals**:  
  - Game rules: `GameBoard`.  
  - Rendering: `BoardVisualizer`, `InventoryUI`, `CardUI`.  
  - Control flow: `GameManager`.  

- This separation ensures:  
  - Easier debugging.  
  - Bot vs Bot (EvE) mode works without UI clicks.  
  - Visual layer can be replaced (e.g., 3D board) without touching rules.  

---

### 5.6 Future UI Improvements

- Add **animations** (smooth marble placement/movement).  
- Add **sound effects** for clicks and win condition.  
- Improve **mobile UI layout** (bigger buttons, touch input).  
- Highlight **last move** (to help players follow game flow).  
- Add **Undo** option in PvP for casual play.  
- Add **colorblind mode** (patterns/icons on marbles).  

---

## 6. Extending the Game

Ideas for future improvements:  
- Add animations (marble placement, highlighting).  
- Add sound effects and background music.  
- Add multiplayer networking (online PvP).  
- Improve AI heuristics (evaluate board instead of pure rollouts).  
- Add more shapes or special rules.  

---

## 7. Known Issues / Limitations
- Bot may bias toward early moves if iterations are too low.  
- UI scaling may need adjustments on different resolutions.  
- Only two players supported.  

---

## 8. Credits
- Developed in Unity (C#).  
- Author: František Procházka 

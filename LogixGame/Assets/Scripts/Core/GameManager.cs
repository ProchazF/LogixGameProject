using System.Collections;
using System.Collections.Generic;
using System.Linq;
using TMPro;
using UnityEngine;
using UnityEngine.UIElements;

public enum GameMode { PvP, PvE, EvE }
public enum Difficulty { Easy, Normal, Hard }



public class GameManager : MonoBehaviour
{
    private const int width = 7;
    private const int height = 7;
    private const int numberOfWinningCardsInHand = 2;

    private MarbleColor selectedColor = MarbleColor.None;

    public CursorMarble cursorMarble; // Assign in Inspector

    private Vector2Int? pickedUpFrom = null;

    [Header("Spawns")]
    public Transform spawnP1;
    public Transform spawnP2;

    [Header("Prefabs")]
    public GameObject humanPrefab;
    public GameObject botPrefab;

    public WinShapeInstance[] playerACards; // Player cards
    public WinShapeInstance[] playerBCards;

    private GameMode mode;
    private Difficulty botA;   // PvE uses botA
    private Difficulty botB;   // EvE uses both

    public TextMeshProUGUI settingsDisplay;

    // Internal game board for bot and validation
    private GameBoard myBoard;

    // Only the visualizer, won't have insane logic
    public BoardVisualizer boardVisualizer; // drag from scene (e.g., on Canvas or empty GO)
    public InventoryUI inventoryUI;
    public TextMeshProUGUI cardDisplayText;
    public IllegalMarblesUI illegalMarblesUI; // Drag it from scene

    private int currentPlayer = 0; // 0 = Player A, 1 = Player B
    private bool isBotMoving = false;

    [SerializeField] private CardUI cardPrefab;
    [SerializeField] private Transform cardParent; // some UI Panel/empty object in Canvas
    [SerializeField] private Transform playerAContainer;
    [SerializeField] private Transform playerBContainer;

    [SerializeField] private TextMeshProUGUI turnText;
    [SerializeField] private GameObject winPanel;
    [SerializeField] private TextMeshProUGUI winText;

    public static GameManager Instance;

    void Start()
    {
        // Display current config
        /*
        string displayText = $"Mode: {mode}\nBotA: {botA}\nBotB: {botB}";
        Debug.Log(displayText);
        if (settingsDisplay != null)
            settingsDisplay.text = displayText;
        */


        // create internal game board (logic)
        myBoard = new GameBoard(width, height); // or whatever size
        
        // Debug.Log("[GameManager] myBoard initialized: " + (myBoard != null ? "✅ Not null" : "❌ NULL"));


        // Give each player his cards while not allowing duplicates (might have to be for loop for more players)
        playerACards = GeneratePlayerCards();
        var usedShapes = new HashSet<WinShape>(playerACards.Select(c => c.Shape));
        playerBCards = GeneratePlayerCards(usedShapes);

        // Optional: Show them in console
        Debug.Log("Player A Cards:");
        foreach (var card in playerACards)
            Debug.Log($"🃏 {card.Name} (Blocked Color: {card.AssignedColor})");

        Debug.Log("Player B Cards:");
        foreach (var card in playerBCards)
            Debug.Log($"🃏 {card.Name} (Blocked Color: {card.AssignedColor})");

        /* Show first playerA card
        if (playerACards.Length > 0)
        {
            var card = Instantiate(cardPrefab, cardParent);
            card.Init(playerACards[0]); // show first card
        }
        */

        // Show Player A cards (bottom)
        foreach (var cardInstance in playerACards)
        {
            var cardUI = Instantiate(cardPrefab, playerAContainer);
            cardUI.Init(cardInstance);
        }

        // Show Player B cards (top)
        foreach (var cardInstance in playerBCards)
        {
            var cardUI = Instantiate(cardPrefab, playerBContainer);
            cardUI.Init(cardInstance);
        }


        // TODO: initialize visual board
        if (boardVisualizer != null)
            boardVisualizer.Init(myBoard);
        boardVisualizer.onTileClickedCallback = OnTileClicked;

        // Show Inventory
        //Debug.Log($"InventoryUI: {inventoryUI}, GameBoard: {myBoard}");

        inventoryUI.Init(myBoard.GetInventory());
        inventoryUI.UpdateCount(MarbleColor.Red, myBoard.GetInventory()[MarbleColor.Red]);

        UpdateTurnText();

        boardVisualizer.Refresh(); // Visualize starting position
    }


    void Awake()
    {
        Instance = this;
        // 1) Read selections from PlayerPrefs (defaults are safe)
        string modeStr = PlayerPrefs.GetString("GameMode", "PvP");
        mode = ParseMode(modeStr);
        // For PvE
        botA = ParseDifficulty(PlayerPrefs.GetString("BotA", "Normal"));
        // For EvE:
        botA = ParseDifficulty(PlayerPrefs.GetString("BotA", botA.ToString()));
        botB = ParseDifficulty(PlayerPrefs.GetString("BotB", "Normal"));

        // 2) Spawn according to mode
        switch (mode)
        {
            case GameMode.PvP:
                SpawnHuman(spawnP1);
                SpawnHuman(spawnP2);
                break;

            case GameMode.PvE:
                SpawnHuman(spawnP1);
                SpawnBot(spawnP2, botA);
                break;

            case GameMode.EvE:
                SpawnBot(spawnP1, botA);
                SpawnBot(spawnP2, botB);
                break;
        }

        // 3) TODO next: initialize board, set active player, etc.
        Debug.Log($"Started {mode} | BotA={botA} | BotB={botB}");

    }

    private GameMode ParseMode(string s)
    {
        return s switch
        {
            "PvE" => GameMode.PvE,
            "EvE" => GameMode.EvE,
            _ => GameMode.PvP
        };
    }

    private Difficulty ParseDifficulty(string s)
    {
        return s switch
        {
            "Easy" => Difficulty.Easy,
            "Hard" => Difficulty.Hard,
            _ => Difficulty.Normal
        };
    }

    private WinShapeInstance[] GeneratePlayerCards(HashSet<WinShape> excluded = null)
    {
        var allShapes = WinShapeDatabase.AllShapes;
        var allColors = new[] { MarbleColor.Red, MarbleColor.Blue, MarbleColor.Green, MarbleColor.Yellow };

        var assigned = new List<WinShapeInstance>();

        while (assigned.Count < 2)
        {
            var shape = allShapes[Random.Range(0, allShapes.Count)];

            // Avoid duplicate shapes
            if (assigned.Any(c => c.Shape == shape)) continue;
            if (excluded != null && excluded.Contains(shape)) continue;

            var blockedColor = allColors[Random.Range(0, allColors.Length)];

            assigned.Add(new WinShapeInstance(shape, blockedColor));
        }

        return assigned.ToArray();
    }

    private GameObject SpawnHuman(Transform t)
    {
        var go = Instantiate(humanPrefab, t.position, t.rotation);
        go.name = "HumanPlayer";
        return go;
    }
    
    private GameObject SpawnBot(Transform t, Difficulty diff)
    {
        var go = Instantiate(botPrefab, t.position, t.rotation);
        go.name = $"BotPlayer_{diff}";
        var ai = go.GetComponent<BotController>();
        if (ai != null) ai.SetDifficulty(diff);
        return go;
    }

    private bool IsBotsTurn()
    {
        if (mode == GameMode.PvE && currentPlayer == 1) return true; // bot is Player B
        if (mode == GameMode.EvE) return true; // both bots
        return false;
    }

    public void OnMarbleSelected(MarbleColor color)
    {

        if (IsBotsTurn() || isBotMoving)
        {
            Debug.Log("It’s bot’s turn — ignoring human input.");
            return;
        }

        // Prevent selecting banned colors
        if (myBoard.previousMoveColors.Contains(color))
        {
            Debug.Log($"[GameManager] Cannot select {color} — it was used in the previous move.");
            return; // ignore the click
        }

        if (pickedUpFrom.HasValue)
        {
            // Return picked up marble
            var pos = pickedUpFrom.Value;
            myBoard.SetMarble(pos.x, pos.y, selectedColor);
            pickedUpFrom = null;
            Debug.Log("Cancelled move from board — marble returned to original position.");
        }

        if (selectedColor == color)
        {
            selectedColor = MarbleColor.None;
            cursorMarble.Clear();
            Debug.Log("Deselected marble");
        }
        else
        {
            selectedColor = color;
            cursorMarble.SetColor(color);
            Debug.Log($"Selected marble from inventory: {color}");
        }

        boardVisualizer.Refresh();
    }

    public void OnTileClicked(int x, int y)
    {
        Debug.Log($"[GameManager] Tile clicked at ({x},{y})");

        //if (myBoard == null) Debug.LogError("myBoard is NULL");
        if (myBoard == null)
        {
            Debug.LogError("Clicked too early — myBoard is still null!");
            return;
        }
        if (cursorMarble == null) Debug.LogError("cursorMarble is NULL");
        if (inventoryUI == null) Debug.LogError("inventoryUI is NULL");

        // -------------------------------
        // CASE 1: Nothing selected -> Try pick up a marble
        // -------------------------------
        if (selectedColor == MarbleColor.None)
        {
            bool picked = myBoard.PickUpMarble(x, y, out MarbleColor pickedColor);
            if (picked)
            {
                selectedColor = pickedColor;
                pickedUpFrom = new Vector2Int(x, y); // Save it here
                cursorMarble.SetColor(pickedColor);
                boardVisualizer.Refresh();
            }
            else
            {
                Debug.Log("Cannot pick up marble here.");
            }

            return;
        }

        var current = myBoard.GetMarble(x, y);

        // EXTRA CASE: when picked up marble tries to go back to original position
        if (pickedUpFrom.HasValue && pickedUpFrom.Value == new Vector2Int(x, y))
        {
            RollbackToOriginal();
            Debug.Log("Move cancelled: marble returned to original position.");
            myBoard.PrintDebugBoard();
            return;
        }

        // -------------------------------
        // CASE 2: Moving a marble from one tile to another
        // -------------------------------
        if (pickedUpFrom != null && current == MarbleColor.None)
        {
            Vector2Int from = pickedUpFrom.Value;

            if (myBoard.CanMoveTo(from.x, from.y, x, y))
            {
                bool moved = myBoard.MoveMarble(from.x, from.y, x, y);
                if (moved)
                {
                    Debug.Log($"Moved {selectedColor} from ({from.x},{from.y}) to ({x},{y})");
                    pickedUpFrom = null;
                    AfterMoveSuccess(selectedColor);
                }
                else
                {
                    Debug.LogError("Move was allowed but failed unexpectedly.");
                    RollbackToOriginal();
                }
            }
            else
            {
                Debug.Log("Invalid move. Rolling back.");
                RollbackToOriginal();
            }

            return;
        }

        // -------------------------------
        // CASE 3: Normal placement
        // -------------------------------
        if (current == MarbleColor.None)
        {
            bool placed = myBoard.PlaceMarble(x, y, selectedColor);
            if (placed)
            {
                Debug.Log($"Placed {selectedColor} at ({x}, {y})");
                pickedUpFrom = null;
                AfterMoveSuccess(selectedColor);
            }
            else
            {
                Debug.Log("Invalid placement.");
                // No rollback needed
            }
        }
        // -------------------------------
        // CASE 4: Replacement
        // -------------------------------
        else if (current != selectedColor && current != MarbleColor.Black)
        {
            if (pickedUpFrom == null)
            {
                // Only allow replacement if we selected from inventory
                bool replaced = myBoard.ReplaceMarble(x, y, selectedColor);
                if (replaced)
                {
                    Debug.Log($"Replaced {current} with {selectedColor} at ({x}, {y})");
                    AfterMoveSuccess(selectedColor);
                    inventoryUI.UpdateCount(current, myBoard.GetInventory()[current]);
                }
                else
                {
                    Debug.Log("Invalid replacement from inventory.");
                    ResetSelection();
                }
            }
            else
            {
                // We picked up a marble from the board — replacing is invalid
                Debug.Log("Cannot replace with a marble picked up from board. Rolling back.");
                var pos = pickedUpFrom.Value;
                myBoard.SetMarble(pos.x, pos.y, selectedColor);
                ResetSelection();
                boardVisualizer.Refresh();
            }

            pickedUpFrom = null;
            boardVisualizer.Refresh();
            return;
        }
        // -------------------------------
        // CASE 5: Invalid target
        // -------------------------------
        Debug.Log("Cannot place or replace marble here.");
        RollbackToOriginal(); // Handles both logic and visuals
    }
    private void AfterMoveSuccess(MarbleColor usedColor)
    {
        boardVisualizer.Refresh();

        if (usedColor != MarbleColor.Black)
        {
            var inventory = myBoard.GetInventory();
            if (inventory.ContainsKey(usedColor)) // extra safety
                inventoryUI.UpdateCount(usedColor, inventory[usedColor]);
        }

        selectedColor = MarbleColor.None;
        cursorMarble.Clear();
        pickedUpFrom = null;

        if (illegalMarblesUI != null)
            illegalMarblesUI.SetIllegalMarbles(myBoard.previousMoveColors);

        if (CheckForWin()) return;

        // Switch turn
        currentPlayer = 1 - currentPlayer;
        Debug.Log($"Turn ended. Now it's Player {currentPlayer + 1}'s turn.");
        UpdateTurnText();
        myBoard.PrintDebugBoard(); // Print board after each move
    }

    // CheckForWin retrns true if a player won
    private bool CheckForWin()
    {
        // Check Player A
        if (myBoard.CheckWinFromBlack(playerACards,
            out WinShape matchedCardA, out List<Vector2Int> matchedPositionsA))
        {
            ShowWin("Player 1", matchedCardA.Name, matchedPositionsA);
            return true;
        }

        // Check Player B
        if (myBoard.CheckWinFromBlack(playerBCards,
            out WinShape matchedCardB, out List<Vector2Int> matchedPositionsB))
        {
            string name = mode == GameMode.PvE ? "Bot" : "Player 2";
            if (mode == GameMode.EvE) name = "Bot B";

            ShowWin(name, matchedCardB.Name, matchedPositionsB);
            return true;
        }

        return false; // no win yet
    }
    private void ShowWin(string playerName, string shapeName, List<Vector2Int> positions)
    {
        Debug.Log($"🎉 {playerName} wins with {shapeName}!");

        if (winPanel != null && winText != null)
        {
            winPanel.SetActive(true);
            winText.text = $"{playerName} wins!\nShape: {shapeName}";
        }

        if (boardVisualizer != null && positions != null)
            boardVisualizer.HighlightWin(positions);

        enabled = false; // stop further moves
    }

    private void ShowWinScreen(string playerName, string shapeName, List<Vector2Int> positions)
    {
        if (winPanel != null && winText != null)
        {
            winPanel.SetActive(true);
            winText.text = $"{playerName} wins!\nShape: {shapeName}";
        }

        // You could also highlight matched positions on boardVisualizer
        if (boardVisualizer != null && positions != null)
        {
            boardVisualizer.HighlightWin(positions);
        }
    }

    private void RollbackToOriginal()
    {
        if (pickedUpFrom.HasValue && selectedColor != MarbleColor.None)
        {
            var pos = pickedUpFrom.Value;
            myBoard.SetMarble(pos.x, pos.y, selectedColor);
            pickedUpFrom = null;
            ResetSelection();
            boardVisualizer.Refresh();
            Debug.Log("Rollback: marble returned to original position.");
        }
    }

    private void ResetSelection()
    {
        selectedColor = MarbleColor.None;
        cursorMarble.Clear();
    }
    public bool IsPickedUpFrom(Vector2Int pos)
    {
        return pickedUpFrom.HasValue && pickedUpFrom.Value == pos;
    }

    private void UpdateTurnText()
    {
        string who;
        if (mode == GameMode.PvP)
            who = currentPlayer == 0 ? "Player 1" : "Player 2";
        else if (mode == GameMode.PvE)
            who = currentPlayer == 0 ? "Player (You)" : "Bot";
        else // EvE
            who = currentPlayer == 0 ? "Bot A" : "Bot B";

        turnText.text = $"Turn: {who}";
    }

}

using System.Collections.Generic;
using System.Linq;
using TMPro;
using UnityEngine;

public enum GameMode { PvP, PvE, EvE }
public enum Difficulty { Easy, Normal, Hard }



public class GameManager : MonoBehaviour
{
    private const int width = 7;
    private const int height = 7;
    private const int numberOfWinningCardsInHand = 2;

    private MarbleColor selectedColor = MarbleColor.None;

    public CursorMarble cursorMarble; // Assign in Inspector

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

        // Give each player his cards while not allowing duplicates (might have to be for loop for more players)
        playerACards = GeneratePlayerCards();
        var usedShapes = new HashSet<WinShape>(playerACards.Select(c => c.Shape));
        playerBCards = GeneratePlayerCards(usedShapes);

        /* Optional: Show them in console
        Debug.Log("Player A Cards:");
        foreach (var card in playerACards)
            Debug.Log($"🃏 {card.Name} (Blocked Color: {card.AssignedColor})");

        Debug.Log("Player B Cards:");
        foreach (var card in playerBCards)
            Debug.Log($"🃏 {card.Name} (Blocked Color: {card.AssignedColor})");


        // Show on screen
        if (cardDisplayText != null)
        {
            cardDisplayText.text = "<b>Player A Cards:</b>\n";
            foreach (var c in playerACards)
                cardDisplayText.text += $"{c.Name} ≠ {c.AssignedColor}\n";

            cardDisplayText.text += "\n<b>Player B Cards:</b>\n";
            foreach (var c in playerBCards)
                cardDisplayText.text += $"{c.Name} ≠ {c.AssignedColor}\n";
        }
        */

        // TODO: initialize visual board
        if (boardVisualizer != null)
            boardVisualizer.Init(myBoard);
        boardVisualizer.onTileClickedCallback = OnTileClicked;

        Debug.Log($"InventoryUI: {inventoryUI}, GameBoard: {myBoard}");

        inventoryUI.Init(myBoard.GetInventory());
        inventoryUI.UpdateCount(MarbleColor.Red, myBoard.GetInventory()[MarbleColor.Red]);



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

    public void OnMarbleSelected(MarbleColor color)
    {
        if (selectedColor == color)
        {
            // Deselect if clicking same color again
            selectedColor = MarbleColor.None;
            cursorMarble.Clear();
            Debug.Log("Deselected marble");
        }
        else
        {
            selectedColor = color;
            cursorMarble.SetColor(color);
            Debug.Log($"Selected marble: {color}");
        }
    }

    public void OnTileClicked(int x, int y)
    {
        Debug.Log($"[GameManager] Tile clicked at ({x},{y})");

        if (myBoard == null) Debug.LogError("myBoard is NULL");
        if (cursorMarble == null) Debug.LogError("cursorMarble is NULL");
        if (inventoryUI == null) Debug.LogError("inventoryUI is NULL");

        if (selectedColor == MarbleColor.None)
        {
            Debug.Log("No marble selected.");
            return;
        }

        bool success = myBoard.PlaceMarble(x, y, selectedColor);
        if (success)
        {
            Debug.Log($"Placed {selectedColor} at ({x}, {y})");

            // Update visuals
            boardVisualizer.Refresh();
            inventoryUI.UpdateCount(selectedColor, myBoard.GetInventory()[selectedColor]);

            // Clear selection (if desired)
            selectedColor = MarbleColor.None;
            cursorMarble.Clear();

            // Optional: check win
            /*if (myBoard.CheckWinFromBlack(allCards.ToArray(), out var matchedCard, out var positions))
            {
                Debug.Log($"Player won with card: {matchedCard.Name}");
                // TODO: show win screen or end game
            }
            */
            // Switch turn, update color restrictions, etc...
            // EndTurn();
        }
        else
        {
            Debug.Log("Invalid move.");
        }
    }

}

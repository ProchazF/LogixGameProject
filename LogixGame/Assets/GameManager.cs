using System.Collections.Generic;
using TMPro;
using UnityEngine;

public enum GameMode { PvP, PvE, EvE }
public enum Difficulty { Easy, Normal, Hard }



public class GameManager : MonoBehaviour
{
    private const int width = 7;
    private const int height = 7;
    [Header("Spawns")]
    public Transform spawnP1;
    public Transform spawnP2;

    [Header("Prefabs")]
    public GameObject humanPrefab;
    public GameObject botPrefab;

    private GameMode mode;
    private Difficulty botA;   // PvE uses botA
    private Difficulty botB;   // EvE uses both

    public TextMeshProUGUI settingsDisplay;

    // Internal game board for bot and validation
    private GameBoard myBoard;
    // Only the visualizer, won't have insane logic
    public BoardVisualizer boardVisualizer; // drag from scene (e.g., on Canvas or empty GO)

    void Start()
    {
        // Display current config
        string displayText = $"Mode: {mode}\nBotA: {botA}\nBotB: {botB}";
        Debug.Log(displayText);
        if (settingsDisplay != null)
            settingsDisplay.text = displayText;

        // TODO: create internal game board (logic)
        GameBoard myBoard = new GameBoard(width, height); // or whatever size

        // TODO: initialize visual board
        if (boardVisualizer != null)
            boardVisualizer.Init(myBoard);
    }


    void Awake()
    {
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

    /*
     * 
     * Game logic here
     * 
     */


    private bool IsValidCoord(int x, int y)
    {
        return x >= 0 && y >= 0 && x < width && y < height;
    }

    // Check if marble is blocked from all sides
    public bool IsBlocked(int x, int y)
    {
        if (!IsValidCoord(x, y)) return true;
        if (myBoard.board[x, y] == MarbleColor.None) return true;

        Vector2Int[] directions = {
        new Vector2Int(0, 1),   // up
        new Vector2Int(0, -1),  // down
        new Vector2Int(1, 0),   // right
        new Vector2Int(-1, 0)   // left
        };

        foreach (var dir in directions)
        {
            int nx = x + dir.x;
            int ny = y + dir.y;
            if (IsValidCoord(nx, ny) && myBoard.board[nx, ny] == MarbleColor.None)
                return false; // not blocked
        }

        return true;
    }

    // Check if a marble can move to other spot (checks path, not adjacency)
    public bool IsPathThroughEmptyTiles(int fromX, int fromY, int toX, int toY)
    {
        if (!IsValidCoord(fromX, fromY) || !IsValidCoord(toX, toY))
            return false;

        if (myBoard.board[toX, toY] != MarbleColor.None)
            return false; // destination must be empty


        var visited = new HashSet<Vector2Int>();
        var queue = new Queue<Vector2Int>();
        queue.Enqueue(new Vector2Int(fromX, fromY));
        visited.Add(new Vector2Int(fromX, fromY));

        Vector2Int[] directions = {
        new Vector2Int(0, 1),
        new Vector2Int(0, -1),
        new Vector2Int(1, 0),
        new Vector2Int(-1, 0)
    };

        while (queue.Count > 0)
        {
            var current = queue.Dequeue();

            foreach (var dir in directions)
            {
                Vector2Int next = current + dir;
                if (!IsValidCoord(next.x, next.y)) continue;
                if (visited.Contains(next)) continue;

                // You can only step into empty tiles (or the destination)
                if (myBoard.board[next.x, next.y] == MarbleColor.None || (next.x == toX && next.y == toY))
                {
                    if (next.x == toX && next.y == toY)
                        return true;

                    visited.Add(next);
                    queue.Enqueue(next);
                }
            }
        }

        return false; // no path found
    }

    public bool CanMoveTo(int fromX, int fromY, int toX, int toY)
    {
        if (!IsValidCoord(fromX, fromY) || !IsValidCoord(toX, toY)) return false;
        if (board[fromX, fromY] == MarbleColor.None) return false;
        if (board[toX, toY] != MarbleColor.None) return false;
        if (IsBlocked(fromX, fromY)) return false;

        // NEW: only through empty tiles
        if (!IsPathThroughEmptyTiles(fromX, fromY, toX, toY)) return false;

        // Simulate move to check adjacency
        var color = board[fromX, fromY];
        board[fromX, fromY] = MarbleColor.None;
        board[toX, toY] = color;

        bool valid = IsAdjacentToAnyMarble(toX, toY);

        board[toX, toY] = MarbleColor.None;
        board[fromX, fromY] = color;

        return valid;
    }

}

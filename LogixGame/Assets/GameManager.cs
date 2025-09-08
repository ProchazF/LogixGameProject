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
}

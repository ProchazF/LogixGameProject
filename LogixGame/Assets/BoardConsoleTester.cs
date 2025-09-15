using System.Collections.Generic;
using TMPro;
using UnityEngine;

public class BoardConsoleTester : MonoBehaviour
{
    public GameBoard gameBoard;

    public TMP_InputField inputField;
    public TextMeshProUGUI boardDisplay;

    public WinShapeInstance[] testPlayerCards;  // assign these in Inspector or Start()
    private void Start()
    {
        gameBoard = new GameBoard(7, 7);
        gameBoard.PlaceMarble(3, 3, MarbleColor.Black); // Start with black in center
        // Example assignment if not set in inspector:
        if(testPlayerCards == null || testPlayerCards.Length < 2)
{
            testPlayerCards = new[]
            {
        new WinShapeInstance(WinShapeDatabase.AllShapes[0], MarbleColor.Red),   // Line, blocked Red
        new WinShapeInstance(WinShapeDatabase.AllShapes[1], MarbleColor.Blue)  // Plus, blocked Blue
    };
        }

        ShowPlayerCards();
        RedrawBoard();
    }

    public void OnCommandSubmitted()
    {
        string cmd = inputField.text.Trim().ToLower();
        inputField.text = "";

        string[] parts = cmd.Split(' ');

        if (parts.Length == 0) return;

        bool result = false;

        switch (parts[0])
        {
            case "place":
                if (parts.Length == 4)
                {
                    int x = int.Parse(parts[1]);
                    int y = int.Parse(parts[2]);
                    MarbleColor color = ParseColor(parts[3]);
                    result = gameBoard.PlaceMarble(x, y, color);
                }
                break;

            case "move":
                if (parts.Length == 5)
                {
                    int fx = int.Parse(parts[1]);
                    int fy = int.Parse(parts[2]);
                    int tx = int.Parse(parts[3]);
                    int ty = int.Parse(parts[4]);
                    result = gameBoard.MoveMarble(fx, fy, tx, ty);
                }
                break;

            case "replace":
                if (parts.Length == 4)
                {
                    int x = int.Parse(parts[1]);
                    int y = int.Parse(parts[2]);
                    MarbleColor color = ParseColor(parts[3]);
                    result = gameBoard.ReplaceMarble(x, y, color);
                }
                break;

            case "check":
                if (gameBoard.CheckWinFromBlack(testPlayerCards, out var winCard, out var winPositions))
                {
                    Debug.Log($"✅ WIN DETECTED! Matched card: {winCard.Name}");
                    HighlightWinInBoardDisplay(winPositions);
                }
                else
                {
                    Debug.Log("❌ No win found.");
                }
                break;
        }

        if (parts[0] != "check")
        {
            Debug.Log($"Command '{cmd}' result: {result}");
        }
        RedrawBoard();
    }

    private void RedrawBoard()
    {
        string s = "";
        for (int y = 6; y >= 0; y--)
        {
            for (int x = 0; x < 7; x++)
            {
                var marble = gameBoard.GetMarble(x, y);
                s += MarbleChar(marble) + " ";
            }
            s += "\n";
        }
        boardDisplay.text = s;
    }

    private string MarbleChar(MarbleColor color)
    {
        return color switch
        {
            MarbleColor.Red => "R",
            MarbleColor.Blue => "B",
            MarbleColor.Green => "G",
            MarbleColor.Yellow => "Y",
            MarbleColor.Grey => "X",
            MarbleColor.Black => "K",
            _ => "."
        };
    }

    private MarbleColor ParseColor(string s)
    {
        return s switch
        {
            "red" => MarbleColor.Red,
            "blue" => MarbleColor.Blue,
            "green" => MarbleColor.Green,
            "yellow" => MarbleColor.Yellow,
            "gray" => MarbleColor.Grey,
            "grey" => MarbleColor.Grey,
            "black" => MarbleColor.Black,
            _ => MarbleColor.None
        };
    }
    private void HighlightWinInBoardDisplay(List<Vector2Int> winPositions)
    {
        string s = "";
        for (int y = 6; y >= 0; y--)
        {
            for (int x = 0; x < 7; x++)
            {
                var marble = gameBoard.GetMarble(x, y);
                var pos = new Vector2Int(x, y);
                if (winPositions.Contains(pos))
                    s += $"[{MarbleChar(marble)}]";  // Brackets around winning marbles
                else
                    s += $" {MarbleChar(marble)} ";
            }
            s += "\n";
        }
        boardDisplay.text = s;
    }

    private void ShowPlayerCards()
    {
        Debug.Log("🃏 Player Cards:");
        foreach (var card in testPlayerCards)
        {
            Debug.Log($"- {card.Name}");
        }
    }
}

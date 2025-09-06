using System.Drawing;
using UnityEngine;

public enum MarbleColor
{
    None,       // empty
    Red,
    Blue,
    Green,
    Yellow,
    Grey,       // joker
    Black       // fixed in center at start
}
public class GameBoard : MonoBehaviour
{
    private MarbleColor[,] board;

    public int width, height;

    public GameBoard(int width, int height)
    {
        this.width = width;
        this.height = height;
        board = new MarbleColor[width, height];
        InitializeBoard();
    }

    // Initialize the initial board state
    private void InitializeBoard()
    {
        // Place black marble in the center
        int widthCenter = width / 2;
        int heightCenter = height / 2;
        board[widthCenter, heightCenter] = MarbleColor.Black;
    }
    public MarbleColor GetMarble(int x, int y)
    {
        if (!IsValidCoord(x, y)) return MarbleColor.None;
        return board[x, y];
    }

    public bool PlaceMarble(int x, int y, MarbleColor color)
    {
        if (!IsValidCoord(x, y)) return false;
        if (board[x, y] != MarbleColor.None) return false; // already occupied
        board[x, y] = color;
        return true;
    }

    private bool IsValidCoord(int x, int y)
    {
        return x >= 0 && y >= 0 && x < width && y < height;
    }

    public bool IsAdjacentToAnyMarble(int x, int y)
    {
        if (!IsValidCoord(x, y)) return false;

        // Check the 4 orthogonal directions
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
            if (IsValidCoord(nx, ny) && board[nx, ny] != MarbleColor.None)
            {
                return true;
            }
        }

        return false;
    }

    public void PrintDebugBoard()
    {
        string debug = "";
        for (int y = height - 1; y >= 0; y--)
        {
            for (int x = 0; x < width; x++)
            {
                debug += board[x, y].ToString().Substring(0, 1) + " ";
            }
            debug += "\n";
        }
        Debug.Log(debug);
    }
}

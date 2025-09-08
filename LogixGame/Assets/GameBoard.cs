/*
 * GameBoard.cs
 * Here is the internal structure oif the game, the board and the rules, which the marbles follow
 */


using System.Collections.Generic;
using System.Drawing;
using UnityEngine;
using UnityEngine.InputSystem;

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
    // the board itself
    private MarbleColor[,] board;

    // board sizes
    public int width, height;

    // Tracker of colors with which the prevcious player played with
    private List<MarbleColor> previousMoveColors = new List<MarbleColor>();

    private MarbleInventory marbleInventory;


    public GameBoard(int width, int height)
    {
        this.width = width;
        this.height = height;
        board = new MarbleColor[width, height];
        marbleInventory = new MarbleInventory();
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
    // Returns marble color on a specific spot
    public MarbleColor GetMarble(int x, int y)
    {
        if (!IsValidCoord(x, y)) return MarbleColor.None;
        return board[x, y];
    }

    // Move itself, take a Marble from "inventory" and place it to board
    public bool PlaceMarble(int x, int y, MarbleColor color)
    {
        if (!IsValidCoord(x, y)) return false;
        if (board[x, y] != MarbleColor.None) return false; // already occupied

        // Enforce adjacency rule
        if (!IsAdjacentToAnyMarble(x, y)) return false;

        // Enforce color restriction rule
        if (!IsColorAllowed(color)) return false;

        if (!marbleInventory.Has(color)) return false;

        board[x, y] = color;

        marbleInventory.Use(color); // Update inventory

        RecordMoveColors(color);  // track used color (even Black)
        return true;
    }

    // Another move on board, take a Marble and move it someplace else, acording to rules
    public bool MoveMarble(int fromX, int fromY, int toX, int toY)
    {
        if (!CanMoveTo(fromX, fromY, toX, toY)) return false; // Has to be true to be able to make this move

        var color = board[fromX, fromY]; //take the color of the marble you want to move

        // Enforce color restriction rule
        if (!IsColorAllowed(color)) return false;

        board[fromX, fromY] = MarbleColor.None;
        board[toX, toY] = color;

        RecordMoveColors(color);  // track used color (even Black)
        return true;
    }

    // Third and final move possible, replace existing placed marble with diffferent color (not vblack)
    public bool ReplaceMarble(int x, int y, MarbleColor newColor)
    {
        if (!IsValidCoord(x, y)) return false;
        if (board[x, y] == MarbleColor.None) return false;
        if (board[x, y] == MarbleColor.Black) return false; // can't replace black
        // The one placing has to be in inventory
        if (!marbleInventory.Has(newColor)) return false;

        var oldColor = board[x, y];

        // Enforce color restriction rule
        if (!IsColorAllowed(oldColor)) return false;
        if (!IsColorAllowed(newColor)) return false;

        board[x, y] = newColor;

        marbleInventory.Use(newColor); // Use new one
        marbleInventory.AddBack(oldColor); // Put old one back

        RecordMoveColors(oldColor, newColor);
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

    // Change previous colors played with
    public void RecordMoveColors(params MarbleColor[] colors)
    {
        previousMoveColors.Clear();

        foreach (var color in colors)
        {
            // Only store real colors (no None, no Black)
            if (color != MarbleColor.None)
            {
                if (!previousMoveColors.Contains(color))
                    previousMoveColors.Add(color);
            }
        }

        Debug.Log("Recorded colors used in move: " + string.Join(", ", previousMoveColors));
    }
    
    // Function to check if the color was played in previous move (if so it's illegal)
    public bool IsColorAllowed(MarbleColor color)
    {
        return !previousMoveColors.Contains(color);
    }

    // Check if marble is blocked from all sides
    public bool IsBlocked(int x, int y)
    {
        if (!IsValidCoord(x, y)) return true;
        if (board[x, y] == MarbleColor.None) return true;

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
            if (IsValidCoord(nx, ny) && board[nx, ny] == MarbleColor.None)
                return false; // not blocked
        }

        return true;
    }

    // Check if a marble can move to other spot (checks path, not adjacency)
    public bool IsPathThroughEmptyTiles(int fromX, int fromY, int toX, int toY)
    {
        if (!IsValidCoord(fromX, fromY) || !IsValidCoord(toX, toY))
            return false;

        if (board[toX, toY] != MarbleColor.None)
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
                if (board[next.x, next.y] == MarbleColor.None || (next.x == toX && next.y == toY))
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

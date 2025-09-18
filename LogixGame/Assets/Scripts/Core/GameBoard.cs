/*
 * GameBoard.cs
 * Here is the internal structure oif the game, the board and the rules, which the marbles follow
 */


using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using Unity.VisualScripting;
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
public class GameBoard
{
    // the board itself
    private MarbleColor[,] board;

    // board sizes
    public int width, height;

    // Tracker of colors with which the prevcious player played with
    public List<MarbleColor> previousMoveColors = new List<MarbleColor>();

    private MarbleInventory marbleInventory;

    private static readonly Vector2Int[] Directions = {
        new(0,1), new(1,0), new(0,-1), new(-1,0)
    };


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
    // returns the board
    public MarbleColor[,] GetBoard()
    {
        return board;
    }

    // Returns marble color on a specific spot
    public MarbleColor GetMarble(int x, int y)
    {
        if (!IsValidCoord(x, y)) return MarbleColor.None;
        return board[x, y];
    }

    public void SetMarble(int x, int y, MarbleColor color)
    {
        if (IsValidCoord(x, y))
            board[x, y] = color;
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

    public bool CanReplaceMarble(int x, int y, MarbleColor newColor)
    {
        if (!IsValidCoord(x, y)) return false;

        var existing = board[x, y];

        // Can't replace if it's empty or black
        if (existing == MarbleColor.None || existing == MarbleColor.Black)
            return false;

        // Can't replace same color
        if (existing == newColor)
            return false;

        // You must have the new marble in inventory
        if (!marbleInventory.Has(newColor))
            return false;

        // Color restriction rule
        if (!IsColorAllowed(existing) || !IsColorAllowed(newColor))
            return false;

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

    public bool CanPickUp(int x, int y, out MarbleColor color)
    {
        color = GetMarble(x, y);

        // Can't pick up empty
        if (color == MarbleColor.None)
            return false;

        if (!IsColorAllowed(color))
            return false;

        if (IsBlocked(x, y) == true)
            return false;

        return true;
    }

    public bool PickUpMarble(int x, int y, out MarbleColor pickedColor)
    {
        pickedColor = MarbleColor.None;

        if (!CanPickUp(x, y, out var color))
            return false;

        pickedColor = color;
        
        // board[x, y] = MarbleColor.None;

        return true;
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

    private bool IsWithinBounds(List<Vector2Int> positions)
    {
        return positions.All(p => p.x >= 0 && p.y >= 0 && p.x < width && p.y < height);
    }

    private bool IsInsideBounds(Vector2Int pos)
    {
        return pos.x >= 0 && pos.x < width && pos.y >= 0 && pos.y < height;
    }


    private bool MatchesShapeWithRules(List<MarbleColor> marbles, List<Vector2Int> positions, MarbleColor blockedColor, out MarbleColor matchedColor)
    {
        matchedColor = MarbleColor.None;

        // Allow gray and black as wildcards
        var trueColors = marbles
            .Where(m => m != MarbleColor.Grey && m != MarbleColor.Black)
            .Distinct()
            .ToList();

        // More than one non-wild color → invalid
        if (trueColors.Count > 1) return false;

        // Shape must include black
        if (!marbles.Contains(MarbleColor.Black)) return false;

        // If the only real color is the blocked color → invalid
        if (trueColors.Count == 1 && trueColors[0] == blockedColor)
            return false;

        matchedColor = trueColors.Count == 1 ? trueColors[0] : MarbleColor.Grey;

        // Check isolation: no neighbors of same color (excluding shape positions)
        foreach (var pos in positions)
        {
            foreach (var dir in Directions)
            {
                var neighbor = pos + dir;
                if (!IsInsideBounds(neighbor)) continue;
                if (positions.Contains(neighbor)) continue;

                var neighborColor = board[neighbor.x, neighbor.y];
                if (neighborColor == matchedColor) return false;
            }
        }

        return true;
    }
    public bool CheckWinFromBlack(WinShapeInstance[] cards, out WinShape matchedCard, out List<Vector2Int> matchedPositions)
    {
        matchedCard = null;
        matchedPositions = null;

        // Step 1: Find all black marbles on the board
        List<Vector2Int> blackPositions = new();
        for (int y = 0; y < height; y++)
        {
            for (int x = 0; x < width; x++)
            {
                if (board[x, y] == MarbleColor.Black)
                    blackPositions.Add(new Vector2Int(x, y));
            }
        }

        // Step 2: Try matching each card (with rotations) at each black marble
        foreach (var black in blackPositions)
        {
            foreach (var card in cards)
            {
                foreach (var rotation in card.Shape.Rotations)
                {
                    for (int i = 0; i < rotation.Length; i++) 
                    {
                        // Try to align black marble with each offset in shape
                        Vector2Int offsetToAlign = black - rotation[i];
                        List<Vector2Int> shapePositions = rotation
                            .Select(p => p + offsetToAlign).ToList();

                        if (!IsWithinBounds(shapePositions)) continue;

                        List<MarbleColor> marbles = shapePositions
                            .Select(p => board[p.x, p.y]).ToList();

                        if (!marbles.Contains(MarbleColor.Black)) continue;

                        if (MatchesShapeWithRules(marbles, shapePositions, card.AssignedColor, out MarbleColor matchedColor))
                        {
                            matchedCard = card.Shape;
                            matchedPositions = shapePositions;
                            return true;
                        }
                    }
                }
            }
        }

        return false;
    }

    public List<Move> GetLegalMoves()
    {
        var moves = new List<Move>();

        // --- Place moves ---
        var inventory = marbleInventory.GetAllCounts();
        for (int x = 0; x < width; x++)
        {
            for (int y = 0; y < height; y++)
            {
                if (board[x, y] != MarbleColor.None) continue;
                if (!IsAdjacentToAnyMarble(x, y)) continue;

                foreach (var kv in inventory)
                {
                    MarbleColor color = kv.Key;
                    int count = kv.Value;

                    if (count > 0 && IsColorAllowed(color))
                    {
                        moves.Add(new Move(MoveType.Place, color, null, new Vector2Int(x, y)));
                    }
                }
            }
        }

        // --- Move moves ---
        for (int fx = 0; fx < width; fx++)
        {
            for (int fy = 0; fy < height; fy++)
            {
                MarbleColor color = board[fx, fy];
                if (color == MarbleColor.None) continue;
                if (!IsColorAllowed(color)) continue;
                if (IsBlocked(fx, fy)) continue;

                for (int tx = 0; tx < width; tx++)
                {
                    for (int ty = 0; ty < height; ty++)
                    {
                        if (CanMoveTo(fx, fy, tx, ty))
                        {
                            moves.Add(new Move(MoveType.Move, color, new Vector2Int(fx, fy), new Vector2Int(tx, ty)));
                        }
                    }
                }
            }
        }

        // --- Replace moves ---
        for (int x = 0; x < width; x++)
        {
            for (int y = 0; y < height; y++)
            {
                MarbleColor existing = board[x, y];
                if (existing == MarbleColor.None || existing == MarbleColor.Black) continue;

                foreach (var kv in inventory)
                {
                    MarbleColor color = kv.Key;
                    int count = kv.Value;

                    if (count > 0 && color != existing && IsColorAllowed(color))
                    {
                        if (CanReplaceMarble(x, y, color))
                        {
                            moves.Add(new Move(MoveType.Replace, color, null, new Vector2Int(x, y)));
                        }
                    }
                }
            }
        }

        return moves;
    }

    public void ApplyMove(Move move)
    {
        switch (move.Type)
        {
            case MoveType.Place:
                PlaceMarble(move.To.x, move.To.y, move.Color);
                break;
            case MoveType.Move:
                if (move.From.HasValue)
                    MoveMarble(move.From.Value.x, move.From.Value.y, move.To.x, move.To.y);
                break;
            case MoveType.Replace:
                ReplaceMarble(move.To.x, move.To.y, move.Color);
                break;
        }
    }

    public GameBoard Clone()
    {
        var copy = new GameBoard(width, height);
        copy.board = (MarbleColor[,])this.board.Clone();
        copy.marbleInventory = this.marbleInventory.Clone();
        copy.previousMoveColors = new List<MarbleColor>(this.previousMoveColors);
        return copy;
    }

    // Get inventory
    public Dictionary<MarbleColor, int> GetInventory()
    {
        return marbleInventory.GetAllCounts();
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

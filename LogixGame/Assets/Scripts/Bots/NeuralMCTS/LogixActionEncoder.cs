using System;
using UnityEngine;

public static class LogixActionEncoder
{
    public const int BoardSize = 7;
    public const int CellCount = BoardSize * BoardSize;
    public const int ColorCount = 5;

    public const int PlaceOffset = 0;
    public const int PlaceSize =
        CellCount * ColorCount; // 49 * 5 = 245

    public const int MoveOffset =
        PlaceOffset + PlaceSize; // 245

    public const int MoveSize =
        CellCount * CellCount; // 49 * 49 = 2401

    public const int ReplaceOffset =
        MoveOffset + MoveSize; // 2646

    public const int ReplaceSize =
        CellCount * ColorCount; // 245

    public const int ActionCount =
        PlaceSize + MoveSize + ReplaceSize; // 2891

    private static readonly MarbleColor[] ColorOrder =
    {
        MarbleColor.Red,
        MarbleColor.Green,
        MarbleColor.Blue,
        MarbleColor.Yellow,
        MarbleColor.Grey
    };

    /// <summary>
    /// Converts a Unity Move into the policy index used by the ONNX model.
    /// </summary>
    public static int EncodeMove(Move move)
    {
        if (move == null)
        {
            throw new ArgumentNullException(nameof(move));
        }

        switch (move.Type)
        {
            case MoveType.Place:
                return EncodePlace(
                    move.To.x,
                    move.To.y,
                    move.Color
                );

            case MoveType.Move:
                if (!move.From.HasValue)
                {
                    throw new ArgumentException(
                        "A move action must have a source position.",
                        nameof(move)
                    );
                }

                return EncodeMovement(
                    move.From.Value.x,
                    move.From.Value.y,
                    move.To.x,
                    move.To.y
                );

            case MoveType.Replace:
                return EncodeReplace(
                    move.To.x,
                    move.To.y,
                    move.Color
                );

            default:
                throw new ArgumentOutOfRangeException(
                    nameof(move),
                    move.Type,
                    "Unknown move type."
                );
        }
    }

    public static int EncodePlace(
        int x,
        int y,
        MarbleColor color)
    {
        ValidateCoordinates(x, y);

        int cellIndex = CellToIndex(y, x);
        int colorIndex = ColorToIndex(color);

        return
            PlaceOffset +
            cellIndex * ColorCount +
            colorIndex;
    }

    public static int EncodeMovement(
        int fromX,
        int fromY,
        int toX,
        int toY)
    {
        ValidateCoordinates(fromX, fromY);
        ValidateCoordinates(toX, toY);

        int fromIndex = CellToIndex(fromY, fromX);
        int toIndex = CellToIndex(toY, toX);

        return
            MoveOffset +
            fromIndex * CellCount +
            toIndex;
    }

    public static int EncodeReplace(
        int x,
        int y,
        MarbleColor color)
    {
        ValidateCoordinates(x, y);

        int cellIndex = CellToIndex(y, x);
        int colorIndex = ColorToIndex(color);

        return
            ReplaceOffset +
            cellIndex * ColorCount +
            colorIndex;
    }

    /// <summary>
    /// Converts a policy index back into a Unity Move.
    ///
    /// Decoded actions are not guaranteed to be legal in the current state.
    /// Legality must still be checked using GameBoard.GetLegalMoves().
    /// </summary>
    public static Move DecodeAction(int actionIndex)
    {
        ValidateActionIndex(actionIndex);

        if (actionIndex < MoveOffset)
        {
            return DecodePlace(actionIndex);
        }

        if (actionIndex < ReplaceOffset)
        {
            return DecodeMovement(actionIndex);
        }

        return DecodeReplace(actionIndex);
    }

    private static Move DecodePlace(int actionIndex)
    {
        int localIndex = actionIndex - PlaceOffset;

        int cellIndex = localIndex / ColorCount;
        int colorIndex = localIndex % ColorCount;

        IndexToCell(
            cellIndex,
            out int row,
            out int column
        );

        MarbleColor color = IndexToColor(colorIndex);

        return new Move(
            MoveType.Place,
            color,
            null,
            new Vector2Int(column, row)
        );
    }

    private static Move DecodeMovement(int actionIndex)
    {
        int localIndex = actionIndex - MoveOffset;

        int fromIndex = localIndex / CellCount;
        int toIndex = localIndex % CellCount;

        IndexToCell(
            fromIndex,
            out int fromRow,
            out int fromColumn
        );

        IndexToCell(
            toIndex,
            out int toRow,
            out int toColumn
        );

        /*
         * The Python move action contains no color.
         *
         * The actual color is determined by the marble at the source cell.
         * MarbleColor.None is therefore used here as a placeholder.
         */
        return new Move(
            MoveType.Move,
            MarbleColor.None,
            new Vector2Int(fromColumn, fromRow),
            new Vector2Int(toColumn, toRow)
        );
    }

    private static Move DecodeReplace(int actionIndex)
    {
        int localIndex = actionIndex - ReplaceOffset;

        int cellIndex = localIndex / ColorCount;
        int colorIndex = localIndex % ColorCount;

        IndexToCell(
            cellIndex,
            out int row,
            out int column
        );

        MarbleColor color = IndexToColor(colorIndex);

        return new Move(
            MoveType.Replace,
            color,
            null,
            new Vector2Int(column, row)
        );
    }

    /// <summary>
    /// Python mapping:
    ///
    /// cellIndex = row * 7 + column
    /// </summary>
    private static int CellToIndex(
        int row,
        int column)
    {
        return row * BoardSize + column;
    }

    private static void IndexToCell(
        int cellIndex,
        out int row,
        out int column)
    {
        if (cellIndex < 0 || cellIndex >= CellCount)
        {
            throw new ArgumentOutOfRangeException(
                nameof(cellIndex),
                cellIndex,
                $"Cell index must be between 0 and {CellCount - 1}."
            );
        }

        row = cellIndex / BoardSize;
        column = cellIndex % BoardSize;
    }

    private static int ColorToIndex(
        MarbleColor color)
    {
        for (int i = 0; i < ColorOrder.Length; i++)
        {
            if (ColorOrder[i] == color)
            {
                return i;
            }
        }

        throw new ArgumentException(
            $"Color {color} cannot be encoded as a policy action. " +
            "Only Red, Green, Blue, Yellow and Grey are supported.",
            nameof(color)
        );
    }

    private static MarbleColor IndexToColor(
        int colorIndex)
    {
        if (colorIndex < 0 ||
            colorIndex >= ColorOrder.Length)
        {
            throw new ArgumentOutOfRangeException(
                nameof(colorIndex),
                colorIndex,
                $"Color index must be between 0 and " +
                $"{ColorOrder.Length - 1}."
            );
        }

        return ColorOrder[colorIndex];
    }

    private static void ValidateCoordinates(
        int x,
        int y)
    {
        if (x < 0 || x >= BoardSize ||
            y < 0 || y >= BoardSize)
        {
            throw new ArgumentOutOfRangeException(
                $"Coordinates ({x}, {y}) are outside the " +
                $"{BoardSize}x{BoardSize} board."
            );
        }
    }

    private static void ValidateActionIndex(
        int actionIndex)
    {
        if (actionIndex < 0 ||
            actionIndex >= ActionCount)
        {
            throw new ArgumentOutOfRangeException(
                nameof(actionIndex),
                actionIndex,
                $"Action index must be between 0 and " +
                $"{ActionCount - 1}."
            );
        }
    }
}
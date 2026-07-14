using System;
using System.Collections.Generic;
using UnityEngine;

public static class LogixStateEncoder
{
    public const int BoardSize = 7;
    public const int BoardChannels = 6;

    public const int BannedFeatureCount = 5;
    public const int InventoryFeatureCount = 5;
    public const int PlayerFeatureCount = 1;

    public const int ShapeCount = 18;
    public const int AssignedColorCount = 4;
    public const int ObjectiveCount = 4;

    public const int ObjectiveFeatureCount =
        ObjectiveCount * (ShapeCount + AssignedColorCount);

    public const int FeatureCount =
        BannedFeatureCount +
        InventoryFeatureCount +
        PlayerFeatureCount +
        ObjectiveFeatureCount;

    private static readonly MarbleColor[] ColorOrder =
    {
        MarbleColor.Red,
        MarbleColor.Green,
        MarbleColor.Blue,
        MarbleColor.Yellow,
        MarbleColor.Grey
    };

    private static readonly MarbleColor[] AssignedColorOrder =
    {
        MarbleColor.Red,
        MarbleColor.Green,
        MarbleColor.Blue,
        MarbleColor.Yellow
    };

    private static readonly string[] ShapeNames =
    {
        "Line",
        "Plus",
        "T-Shape",
        "Long L-Shape Mirrored",
        "Long L-Shape",
        "Short L-Shape",
        "Seven-Shape",
        "Mirrored Seven-Shape",
        "C-Shape",
        "Stair-Shape",
        "Z-Shape",
        "Reverse Z-Shape",
        "One-Shape",
        "Reverse One-Shape",
        "d-shape",
        "b-shape",
        "Snake",
        "Reverse Snake"
    };

    private static readonly Dictionary<string, int> ShapeToIndex =
        CreateShapeIndex();

    public static EncodedLogixState Encode(
        GameBoard board,
        WinShapeInstance[] playerACards,
        WinShapeInstance[] playerBCards,
        int currentPlayer)
    {
        if (board == null)
        {
            throw new ArgumentNullException(nameof(board));
        }

        ValidateBoardSize(board);

        float[] boardPlanes = EncodeBoard(board);

        float[] features = EncodeFeatures(
            board,
            playerACards,
            playerBCards,
            currentPlayer
        );

        return new EncodedLogixState(boardPlanes, features);
    }

    public static float[] EncodeBoard(GameBoard board)
    {
        if (board == null)
        {
            throw new ArgumentNullException(nameof(board));
        }

        ValidateBoardSize(board);

        float[] planes =
            new float[BoardChannels * BoardSize * BoardSize];

        for (int y = 0; y < BoardSize; y++)
        {
            for (int x = 0; x < BoardSize; x++)
            {
                MarbleColor color = board.GetMarble(x, y);

                int channel = GetBoardChannel(color);

                if (channel < 0)
                {
                    continue;
                }

                int index = BoardIndex(channel, y, x);
                planes[index] = 1f;
            }
        }

        return planes;
    }

    public static float[] EncodeFeatures(
        GameBoard board,
        WinShapeInstance[] playerACards,
        WinShapeInstance[] playerBCards,
        int currentPlayer)
    {
        if (board == null)
        {
            throw new ArgumentNullException(nameof(board));
        }

        ValidateCards(playerACards, nameof(playerACards));
        ValidateCards(playerBCards, nameof(playerBCards));

        float[] features = new float[FeatureCount];

        int offset = 0;

        offset = EncodeBannedColors(
            board,
            features,
            offset
        );

        offset = EncodeInventory(
            board,
            features,
            offset
        );

        offset = EncodeCurrentPlayer(
            currentPlayer,
            features,
            offset
        );

        offset = EncodeObjectives(
            playerACards,
            features,
            offset
        );

        offset = EncodeObjectives(
            playerBCards,
            features,
            offset
        );

        if (offset != FeatureCount)
        {
            throw new InvalidOperationException(
                $"State encoding produced {offset} features, " +
                $"but expected {FeatureCount}."
            );
        }

        return features;
    }

    private static int EncodeBannedColors(
        GameBoard board,
        float[] output,
        int offset)
    {
        for (int i = 0; i < ColorOrder.Length; i++)
        {
            MarbleColor color = ColorOrder[i];

            output[offset + i] =
                board.previousMoveColors.Contains(color)
                    ? 1f
                    : 0f;
        }

        return offset + BannedFeatureCount;
    }

    private static int EncodeInventory(
        GameBoard board,
        float[] output,
        int offset)
    {
        Dictionary<MarbleColor, int> inventory =
            board.GetInventory();

        for (int i = 0; i < ColorOrder.Length; i++)
        {
            MarbleColor color = ColorOrder[i];

            output[offset + i] =
                inventory.TryGetValue(color, out int count)
                    ? count
                    : 0;
        }

        return offset + InventoryFeatureCount;
    }

    private static int EncodeCurrentPlayer(
        int currentPlayer,
        float[] output,
        int offset)
    {
        /*
         * Python uses:
         *
         *   +1 for player A
         *   -1 for player B
         *
         * Your Unity game currently appears to use:
         *
         *   0 for player A
         *   1 for player B
         */
        output[offset] = currentPlayer switch
        {
            0 => 1f,
            1 => -1f,
            _ => throw new ArgumentOutOfRangeException(
                nameof(currentPlayer),
                currentPlayer,
                "Current player must be 0 or 1."
            )
        };

        return offset + PlayerFeatureCount;
    }

    private static int EncodeObjectives(
        WinShapeInstance[] cards,
        float[] output,
        int offset)
    {
        foreach (WinShapeInstance card in cards)
        {
            offset = EncodeSingleObjective(
                card,
                output,
                offset
            );
        }

        return offset;
    }

    private static int EncodeSingleObjective(
        WinShapeInstance card,
        float[] output,
        int offset)
    {
        if (card == null)
        {
            return offset + ShapeCount + AssignedColorCount;
        }

        string baseShapeName =
            GetBaseShapeName(card.Name);

        if (ShapeToIndex.TryGetValue(
                baseShapeName,
                out int shapeIndex))
        {
            output[offset + shapeIndex] = 1f;
        }
        else
        {
            Debug.LogWarning(
                $"[LogixStateEncoder] Unknown shape name: " +
                $"'{card.Name}'."
            );
        }

        offset += ShapeCount;

        int assignedColorIndex =
            GetAssignedColorIndex(card.AssignedColor);

        if (assignedColorIndex >= 0)
        {
            output[offset + assignedColorIndex] = 1f;
        }
        else
        {
            Debug.LogWarning(
                $"[LogixStateEncoder] Unsupported assigned color: " +
                $"{card.AssignedColor}."
            );
        }

        return offset + AssignedColorCount;
    }

    private static int BoardIndex(
        int channel,
        int row,
        int column)
    {
        /*
         * Tensor layout:
         *
         * [channel, row, column]
         *
         * flattened as:
         *
         * channel * 49 + row * 7 + column
         */
        return
            channel * BoardSize * BoardSize +
            row * BoardSize +
            column;
    }

    private static int GetBoardChannel(MarbleColor color)
    {
        return color switch
        {
            MarbleColor.Red => 0,
            MarbleColor.Green => 1,
            MarbleColor.Blue => 2,
            MarbleColor.Yellow => 3,
            MarbleColor.Grey => 4,
            MarbleColor.Black => 5,
            _ => -1
        };
    }

    private static int GetAssignedColorIndex(
        MarbleColor color)
    {
        for (int i = 0; i < AssignedColorOrder.Length; i++)
        {
            if (AssignedColorOrder[i] == color)
            {
                return i;
            }
        }

        return -1;
    }

    private static string GetBaseShapeName(
        string shapeName)
    {
        if (string.IsNullOrWhiteSpace(shapeName))
        {
            return string.Empty;
        }

        int rotationSeparator = shapeName.IndexOf('@');

        if (rotationSeparator < 0)
        {
            return shapeName;
        }

        return shapeName.Substring(0, rotationSeparator);
    }

    private static Dictionary<string, int> CreateShapeIndex()
    {
        Dictionary<string, int> result =
            new Dictionary<string, int>();

        for (int i = 0; i < ShapeNames.Length; i++)
        {
            result[ShapeNames[i]] = i;
        }

        return result;
    }

    private static void ValidateBoardSize(GameBoard board)
    {
        if (board.width != BoardSize ||
            board.height != BoardSize)
        {
            throw new ArgumentException(
                $"The neural network expects a " +
                $"{BoardSize}x{BoardSize} board, but received " +
                $"{board.width}x{board.height}."
            );
        }
    }

    private static void ValidateCards(
        WinShapeInstance[] cards,
        string parameterName)
    {
        if (cards == null)
        {
            throw new ArgumentNullException(parameterName);
        }

        /*
         * Python expects exactly two cards for each player:
         *
         * player A: 2
         * player B: 2
         *
         * Total objectives: 4
         */
        if (cards.Length != 2)
        {
            throw new ArgumentException(
                $"Expected exactly 2 cards, but received " +
                $"{cards.Length}.",
                parameterName
            );
        }
    }
}

public readonly struct EncodedLogixState
{
    public float[] BoardPlanes { get; }
    public float[] Features { get; }

    public EncodedLogixState(
        float[] boardPlanes,
        float[] features)
    {
        BoardPlanes = boardPlanes;
        Features = features;
    }
}
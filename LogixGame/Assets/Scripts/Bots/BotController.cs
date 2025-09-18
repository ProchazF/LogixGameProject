using System.Collections.Generic;
using UnityEngine;

public class BotController : MonoBehaviour
{
    private Difficulty difficulty;
    private MCTSBot mctsBot;  // for Normal/Hard

    public void SetDifficulty(Difficulty diff)
    {
        difficulty = diff;
        if (difficulty == Difficulty.Normal)
            mctsBot = new MCTSBot(iterations: 200); // lighter search
        else if (difficulty == Difficulty.Hard)
            mctsBot = new MCTSBot(iterations: 1000); // deeper search
    }

    public Move GetMove(GameBoard board, WinShapeInstance[] playerACards, WinShapeInstance[] playerBCards, int botPlayer)
    {
        List<Move> moves = board.GetLegalMoves();
        if (moves.Count == 0) return null;

        switch (difficulty)
        {
            case Difficulty.Easy:
                return RandomMove(board);

            case Difficulty.Normal:
            case Difficulty.Hard:
                if (mctsBot != null)
                    return mctsBot.GetBestMove(board, playerACards, playerBCards, botPlayer);
                else
                    return RandomMove(board);

            default:
                return RandomMove(board);
        }
    }

    private Move RandomMove(GameBoard board)
    {
        List<Move> moves = board.GetLegalMoves();
        if (moves.Count == 0) return null;
        return moves[Random.Range(0, moves.Count)];
    }

    private Move GreedyMove(GameBoard board)
    {
        // Naive: just find the first legal Place move from inventory
        Dictionary<MarbleColor, int> inv = board.GetInventory();
        for (int x = 0; x < board.width; x++)
        {
            for (int y = 0; y < board.height; y++)
            {
                if (board.GetMarble(x, y) == MarbleColor.None && board.IsAdjacentToAnyMarble(x, y))
                {
                    foreach (var kv in inv)
                    {
                        if (kv.Value > 0 && board.IsColorAllowed(kv.Key))
                        {
                            return new Move(MoveType.Place, kv.Key, null, new Vector2Int(x, y));
                        }
                    }
                }
            }
        }

        // Fallback: no moves found
        return null;
    }
}

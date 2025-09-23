using System.Collections.Generic;
using UnityEngine;

public class BotController : MonoBehaviour
{
    private Difficulty difficulty;
    private const int normalDifficultyIterations = 300;
    private const int highDifficultyIterations = 1000;
    // private MCTSBot mctsBot;  // for Normal/Hard
    private MCTS mcts;

    public void SetDifficulty(Difficulty diff)
    {
        difficulty = diff;
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
                int iterations = difficulty == Difficulty.Normal ? normalDifficultyIterations : highDifficultyIterations;
                MCTS mcts = new MCTS();
                return mcts.Search(board, botPlayer, playerACards, playerBCards, iterations);

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
}

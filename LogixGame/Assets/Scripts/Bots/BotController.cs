using System.Collections.Generic;
using UnityEngine;

public class BotController : MonoBehaviour
{
    private Difficulty difficulty;

    private const int NormalDifficultyDepth = 2;
    private const int HighDifficultyIterations = 200;

    private AlphaBetaBot alphaBetaBot;
    private NeuralMCTSBot neuralMctsBot;

    private bool initialized;

    public void Initialize(LogixNeuralNetwork neuralNetwork)
    {
        alphaBetaBot = new AlphaBetaBot(NormalDifficultyDepth);

        if (neuralNetwork == null)
        {
            Debug.LogError(
                "[BotController] Cannot initialize NeuralMCTSBot: " +
                "LogixNeuralNetwork is null."
            );

            neuralMctsBot = null;
            initialized = false;
            return;
        }

        neuralMctsBot = new NeuralMCTSBot(
            neuralNetwork,
            HighDifficultyIterations
        );

        initialized = true;

        Debug.Log(
            "[BotController] Initialized AlphaBetaBot and NeuralMCTSBot."
        );
    }

    public void SetDifficulty(Difficulty diff)
    {
        difficulty = diff;

        Debug.Log(
            $"[BotController] Difficulty set to {difficulty}."
        );
    }

    public Move GetMove(
        GameBoard board,
        WinShapeInstance[] playerACards,
        WinShapeInstance[] playerBCards,
        int botPlayer)
    {
        if (!initialized)
        {
            Debug.LogError(
                "[BotController] BotController was not initialized. " +
                "Call Initialize() after AddComponent<BotController>()."
            );

            return RandomMove(board);
        }

        if (board == null)
        {
            Debug.LogError("[BotController] GameBoard is null.");
            return null;
        }

        List<Move> legalMoves = board.GetLegalMoves();

        if (legalMoves.Count == 0)
        {
            return null;
        }

        Debug.Log(
            $"[BotController] Getting move. " +
            $"Difficulty={difficulty}, Player={botPlayer}"
        );

        switch (difficulty)
        {
            case Difficulty.Easy:
                return RandomMove(legalMoves);

            case Difficulty.Normal:
                return alphaBetaBot.GetBestMove(
                    board,
                    playerACards,
                    playerBCards,
                    botPlayer
                );

            case Difficulty.Hard:
                if (neuralMctsBot == null)
                {
                    Debug.LogError(
                        "[BotController] NeuralMCTSBot is not available. " +
                        "Returning a random legal move."
                    );

                    return RandomMove(legalMoves);
                }

                return neuralMctsBot.GetBestMove(
                    board,
                    playerACards,
                    playerBCards,
                    botPlayer
                );

            default:
                return RandomMove(legalMoves);
        }
    }

    private Move RandomMove(GameBoard board)
    {
        if (board == null)
        {
            return null;
        }

        return RandomMove(board.GetLegalMoves());
    }

    private Move RandomMove(List<Move> legalMoves)
    {
        if (legalMoves == null || legalMoves.Count == 0)
        {
            return null;
        }

        return legalMoves[Random.Range(0, legalMoves.Count)];
    }
}
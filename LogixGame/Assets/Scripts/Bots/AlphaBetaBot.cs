using System.Collections.Generic;
using UnityEngine;

public class AlphaBetaBot
{
    private readonly int maxDepth;

    private WinShapeInstance[] playerACards;
    private WinShapeInstance[] playerBCards;
    private int botPlayer;

    public AlphaBetaBot(int maxDepth = 3)
    {
        this.maxDepth = maxDepth;
    }

    public Move GetBestMove(
        GameBoard rootBoard,
        WinShapeInstance[] playerACards,
        WinShapeInstance[] playerBCards,
        int currentPlayer)
    {
        this.playerACards = playerACards;
        this.playerBCards = playerBCards;
        botPlayer = currentPlayer;

        List<Move> legalMoves = rootBoard.GetLegalMoves();

        if (legalMoves.Count == 0)
        {
            Debug.LogWarning("[AlphaBeta] No legal moves available.");
            return null;
        }

        Move bestMove = null;
        float bestScore = float.NegativeInfinity;

        float alpha = float.NegativeInfinity;
        float beta = float.PositiveInfinity;

        // Always immediately play a winning move.
        foreach (Move move in legalMoves)
        {
            GameBoard nextState = rootBoard.Clone();
            nextState.ApplyMove(move);

            if (HasPlayerWon(nextState, botPlayer))
            {
                Debug.Log($"[AlphaBeta] Immediate winning move found: {move}");
                return move;
            }
        }

        foreach (Move move in legalMoves)
        {
            GameBoard nextState = rootBoard.Clone();
            nextState.ApplyMove(move);

            float score = AlphaBeta(
                nextState,
                maxDepth - 1,
                alpha,
                beta,
                1 - botPlayer
            );

            Debug.Log($"[AlphaBeta] Move={move}, Score={score:F2}");

            if (score > bestScore)
            {
                bestScore = score;
                bestMove = move;
            }

            alpha = Mathf.Max(alpha, bestScore);
        }

        if (bestMove == null)
        {
            Debug.LogWarning("[AlphaBeta] No best move found. Returning fallback.");
            return legalMoves[0];
        }

        Debug.Log($"[AlphaBeta] Selected={bestMove}, Score={bestScore:F2}");
        return bestMove;
    }

    private float AlphaBeta(
        GameBoard state,
        int depth,
        float alpha,
        float beta,
        int currentPlayer)
    {
        if (HasPlayerWon(state, botPlayer))
        {
            return 100000f + depth;
        }

        int opponent = 1 - botPlayer;

        if (HasPlayerWon(state, opponent))
        {
            return -100000f - depth;
        }

        if (depth <= 0)
        {
            return EvaluateBoard(state);
        }

        List<Move> legalMoves = state.GetLegalMoves();

        if (legalMoves.Count == 0)
        {
            return EvaluateBoard(state);
        }

        bool maximizingPlayer = currentPlayer == botPlayer;

        if (maximizingPlayer)
        {
            float bestScore = float.NegativeInfinity;

            foreach (Move move in legalMoves)
            {
                GameBoard nextState = state.Clone();
                nextState.ApplyMove(move);

                float score = AlphaBeta(
                    nextState,
                    depth - 1,
                    alpha,
                    beta,
                    1 - currentPlayer
                );

                bestScore = Mathf.Max(bestScore, score);
                alpha = Mathf.Max(alpha, bestScore);

                if (beta <= alpha)
                {
                    break;
                }
            }

            return bestScore;
        }
        else
        {
            float bestScore = float.PositiveInfinity;

            foreach (Move move in legalMoves)
            {
                GameBoard nextState = state.Clone();
                nextState.ApplyMove(move);

                float score = AlphaBeta(
                    nextState,
                    depth - 1,
                    alpha,
                    beta,
                    1 - currentPlayer
                );

                bestScore = Mathf.Min(bestScore, score);
                beta = Mathf.Min(beta, bestScore);

                if (beta <= alpha)
                {
                    break;
                }
            }

            return bestScore;
        }
    }

    private float EvaluateBoard(GameBoard state)
    {
        int opponent = 1 - botPlayer;

        if (HasPlayerWon(state, botPlayer))
        {
            return 100000f;
        }

        if (HasPlayerWon(state, opponent))
        {
            return -100000f;
        }

        /*
         * Temporary evaluation:
         *
         * Prefer positions in which the opponent has fewer legal replies.
         * This works without requiring access to the internal board array.
         *
         * You can later replace this with your existing heuristic evaluation,
         * for example by counting matching cells in each player's win shapes.
         */
        int legalMoveCount = state.GetLegalMoves().Count;

        return -legalMoveCount;
    }

    private bool HasPlayerWon(GameBoard state, int player)
    {
        WinShapeInstance[] cards =
            player == 0
                ? playerACards
                : playerBCards;

        return state.CheckWinFromBlack(cards, out _, out _);
    }
}
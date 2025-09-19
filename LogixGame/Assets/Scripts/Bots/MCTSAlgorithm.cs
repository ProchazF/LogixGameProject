using System.Linq;
using System;
using UnityEngine;
using System.Collections.Generic;

public class MCTS
{
    private System.Random rng = new System.Random();

    private const float C = 1.41f; // exploration constant

    private int botPlayer;

    public Move Search(GameBoard rootState, int rootPlayer,
                       WinShapeInstance[] playerACards, WinShapeInstance[] playerBCards,
                       int iterations = 500)
    {
        botPlayer = rootPlayer; // we are searching moves for THIS player
        Debug.Log($"[MCTS] Starting search for bot as Player {botPlayer}");
        MCTSNode root = new MCTSNode(rootState.Clone(), rootPlayer);

        // Expand all root children once
        var legalMoves = root.State.GetLegalMoves();

        // List of safe nodes
        List<MCTSNode> safeChildren = new List<MCTSNode>();

        foreach (var move in legalMoves)
        {
            GameBoard nextState = root.State.Clone();
            nextState.ApplyMove(move);

            // Check for immediate win
            if (rootPlayer == 0 && nextState.CheckWinFromBlack(playerACards, out _, out _))
            {
                Debug.Log("[MCTS] Found instant win as Player 0!");
                return move;
            }
            if (rootPlayer == 1 && nextState.CheckWinFromBlack(playerBCards, out _, out _))
            {
                Debug.Log("[MCTS] Found instant win as Player 1!");
                return move;
            }

            // check If opponent wins
            bool opponentWin = (rootPlayer == 0 && nextState.CheckWinFromBlack(playerBCards, out _, out _))
                || (rootPlayer == 1 && nextState.CheckWinFromBlack(playerACards, out _, out _));

            if (opponentWin)
            {
                Debug.Log($"[MCTS] Move {move} allows opponent to win immediately!");
                // Don't add this child (unless all moves are bad)
                continue;
            }

            // Otherwise create child node for normal search
            var child = new MCTSNode(nextState, 1 - rootPlayer, root, move);
            root.Children.Add(child);
            safeChildren.Add(child);
        }

        // If *all* moves are losing, we have no choice: search anyway
        if (safeChildren.Count == 0)
        {
            Debug.Log("[MCTS] All root moves are bad... searching anyway.");
            foreach (var move in legalMoves)
            {
                GameBoard nextState = root.State.Clone();
                nextState.ApplyMove(move);
                root.Children.Add(new MCTSNode(nextState, 1 - rootPlayer, root, move));
            }
        }

        for (int i = 0; i < iterations; i++)
        {
            // 1. Selection
            MCTSNode node = root;
            while (!node.IsLeaf && node.IsFullyExpanded)
            {
                node = SelectChildUCT(node);
            }

            // 2. Expansion
            if (!node.IsFullyExpanded)
            {
                Move m = node.GetUntriedMove();
                if (m != null)
                {
                    GameBoard nextState = node.State.Clone();
                    nextState.ApplyMove(m);
                    int nextPlayer = 1 - node.Player;
                    node = new MCTSNode(nextState, nextPlayer, node, m);
                    node.Parent.Children.Add(node);
                }
            }

            // 3. Simulation (rollout)
            float result = Rollout(node.State.Clone(), node.Player, playerACards, playerBCards);

            // 4. Backpropagation
            Backpropagate(node, result);
        }

        // Return the move with most visits
        return root.Children.OrderByDescending(c => c.Visits).FirstOrDefault()?.Move;
    }

    private MCTSNode SelectChildUCT(MCTSNode node)
    {
        return node.Children.OrderByDescending(c =>
        {
            if (c.Visits == 0) return float.MaxValue;
            float exploitation = c.Wins / c.Visits;
            float exploration = C * (float)Math.Sqrt(Math.Log(node.Visits + 1) / (c.Visits));
            return exploitation + exploration;
        }).First();
    }

    private float Rollout(GameBoard state, int currentPlayer, WinShapeInstance[] aCards, WinShapeInstance[] bCards)
    {
        int player = currentPlayer;

        // limit rollout depth
        for (int depth = 0; depth < 20; depth++)
        {
            if (state.CheckWinFromBlack(aCards, out var cardA, out var posA))
            {
                return (botPlayer == 0) ? 0f : 1f; // Player A wins
            }
            if (state.CheckWinFromBlack(bCards, out var cardB, out var posB))
            {
                return (botPlayer == 1) ? 0f : 1f; // Player B wins
            }

            var legalMoves = state.GetLegalMoves();
            if (legalMoves.Count == 0)
                return 0.5f; // draw

            Move m = legalMoves[rng.Next(legalMoves.Count)];
            state.ApplyMove(m);
            player = 1 - player;
        }

        return 0.5f; // treat as draw
    }

    private void Backpropagate(MCTSNode node, float result)
    {
        while (node != null)
        {
            node.Visits++;
            // flip perspective: if node.Player is bot, store as win if result is in its favor
            node.Wins += result;
            result = 1 - result; // switch perspective
            node = node.Parent;
        }
    }
}

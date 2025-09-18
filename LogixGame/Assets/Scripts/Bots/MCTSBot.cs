using System.Collections.Generic;
using Unity.VisualScripting;
using UnityEngine;

public class MCTSBot
{
    private class Node
    {
        public GameBoard State;
        public Move Move;              // move that led to this state
        public Node Parent;
        public List<Node> Children = new();
        public int Visits;
        public float Wins;

        public Node(GameBoard state, Move move, Node parent)
        {
            State = state;
            Move = move;
            Parent = parent;
        }

        public bool IsFullyExpanded(List<Move> legalMoves)
        {
            return Children.Count == legalMoves.Count;
        }

        public bool IsLeaf => Children.Count == 0;
    }

    private int iterations;

    public MCTSBot(int iterations = 1000)
    {
        this.iterations = iterations;
    }

    public Move GetBestMove(GameBoard rootBoard, WinShapeInstance[] playerACards, WinShapeInstance[] playerBCards, int currentPlayer)
    {
        Node root = new Node(rootBoard.Clone(), null, null);

        for (int i = 0; i < iterations; i++)
        {
            Node node = Select(root);
            Node expanded = Expand(node, playerACards, playerBCards, currentPlayer);
            float result = Simulate(expanded.State.Clone(), playerACards, playerBCards, currentPlayer);
            Backpropagate(expanded, result);
        }

        if (root.Children.Count == 0)
        {
            Debug.LogError("[MCTS] No children generated! Returning fallback move.");
            var fallbackMoves = rootBoard.GetLegalMoves();
            return fallbackMoves.Count > 0 ? fallbackMoves[0] : null;
        }

        // Pick child with highest visits
        Node bestChild = null;
        int bestVisits = -1;

        foreach (var child in root.Children)
        {
            float winRate = child.Wins / (child.Visits + 1e-6f);
            Debug.Log($"[MCTS] Move {child.Move} => Visits {child.Visits}, Wins {child.Wins}, WR={winRate:F2}");

            if (child.Visits > bestVisits)
            {
                bestVisits = child.Visits;
                bestChild = child;
            }
        }

        Debug.Log($"[MCTS] Selected: {bestChild?.Move}");
        return bestChild?.Move;
    }


    // ------------------- MCTS Steps -------------------

    private Node Select(Node node)
    {
        while (!node.IsLeaf)
        {
            node = BestUCT(node);
        }
        return node;
    }

    // Get all tehj child nodes and check if any of them are winning/losing and play accordingly
    private Node Expand(Node node, WinShapeInstance[] playerACards, WinShapeInstance[] playerBCards, int currentPlayer)
    {
        List<Move> legalMoves = node.State.GetLegalMoves();
        if (legalMoves.Count == 0)
        {
            Debug.LogWarning("[MCTS] No legal moves available — should not happen in Expand!");
            return node; // fail-safe, but game should never reach here
        }

        // 1. Immediate WIN check (always take it!)
        foreach (var move in legalMoves)
        {
            GameBoard testState = node.State.Clone();
            testState.ApplyMove(move);

            if (testState.CheckWinFromBlack(
                    currentPlayer == 0 ? playerACards : playerBCards,
                    out var _, out var _))
            {
                Debug.Log($"[MCTS] Forced WIN found: {move}");

                // make sure it's stored as a child
                Node winChild = new Node(testState, move, node);
                node.Children.Add(winChild);
                return winChild;
            }
        }

        // 2. Expand the first unexpanded move
        foreach (var move in legalMoves)
        {
            if (node.Children.Exists(c => c.Move.Equals(move)))
                continue;

            GameBoard nextState = node.State.Clone();
            nextState.ApplyMove(move);

            Node child = new Node(nextState, move, node);
            node.Children.Add(child);
            return child; // expand only one new child per call
        }

        // 3. All expanded already → pick one randomly (no skipping!)
        return node.Children[Random.Range(0, node.Children.Count)];
    }



    private float Simulate(GameBoard simState, WinShapeInstance[] playerACards, WinShapeInstance[] playerBCards, int startingPlayer)
    {
        int player = startingPlayer;
        int safety = 50; // limit rollout depth

        while (safety-- > 0)
        {
            // Win check for current player
            if (simState.CheckWinFromBlack(player == 0 ? playerACards : playerBCards, out _, out _))
            {
                return 1f; // win for this simulated player
            }
            if (simState.CheckWinFromBlack(player == 1 ? playerACards : playerBCards, out _, out _))
            {
                return 0f; // loss for this simulated player
            }

            var moves = simState.GetLegalMoves();
            if (moves.Count == 0) break;

            var move = moves[Random.Range(0, moves.Count)];
            simState.ApplyMove(move);

            player = 1 - player; // switch turns
        }

        return 0.5f; // draw/unclear
    }


    private void Backpropagate(Node node, float result)
    {
        while (node != null)
        {
            node.Visits++;
            node.Wins += result;
            node = node.Parent;
        }
    }

    private Node BestUCT(Node node)
    {
        Node best = null;
        double bestScore = double.NegativeInfinity;

        foreach (var child in node.Children)
        {
            double exploitation = child.Wins / (child.Visits + 1e-6);
            double exploration = Mathf.Sqrt(2f * Mathf.Log(node.Visits + 1) / (child.Visits + 1e-6f));
            double uctScore = exploitation + exploration;

            Debug.Log($"[MCTS] Move={child.Move}, Visits={child.Visits}, Wins={child.Wins}, Score={uctScore:F3}");

            if (uctScore > bestScore)
            {
                bestScore = uctScore;
                best = child;
            }
        }

        return best;
    }
}

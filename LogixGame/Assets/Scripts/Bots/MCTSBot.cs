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

    public Move GetBestMove(GameBoard rootBoard, WinShapeInstance[] playerACards, WinShapeInstance[] playerBCards, int forPlayer)
    {
        Node root = new Node(rootBoard.Clone(), null, null);

        for (int i = 0; i < iterations; i++)
        {
            Node node = Select(root);
            Node expanded = Expand(node);
            float result = Simulate(expanded.State, playerACards, playerBCards, forPlayer);
            Backpropagate(expanded, result);
        }

        // Pick child with highest visit count
        Node bestChild = null;
        int bestVisits = -1;
        foreach (var child in root.Children)
        {
            if (child.Visits > bestVisits)
            {
                bestVisits = child.Visits;
                bestChild = child;
            }
        }

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

    private Node Expand(Node node)
    {
        List<Move> legalMoves = node.State.GetLegalMoves();
        foreach (var move in legalMoves)
        {
            // Skip if already expanded
            if (node.Children.Exists(c => c.Move != null && c.Move.To == move.To && c.Move.Type == move.Type))
                continue;

            GameBoard nextState = node.State.Clone();
            nextState.ApplyMove(move);

            Node child = new Node(nextState, move, node);
            node.Children.Add(child);
            return child;
        }

        // If no expansion possible, return self
        return node;
    }

    private float Simulate(GameBoard simState, WinShapeInstance[] playerACards, WinShapeInstance[] playerBCards, int forPlayer)
    {
        // Play random moves until terminal (win or no moves)
        int safety = 50; // prevent infinite loop
        while (safety-- > 0)
        {
            // Check win for both players
            if (simState.CheckWinFromBlack(playerACards, out _, out _))
            {
                return forPlayer == 0 ? 1f : 0f; // Player A wins
            }
            if (simState.CheckWinFromBlack(playerBCards, out _, out _))
            {
                return forPlayer == 1 ? 1f : 0f; // Player B wins
            }

            List<Move> moves = simState.GetLegalMoves();
            if (moves.Count == 0) break;

            Move move = moves[Random.Range(0, moves.Count)];
            simState.ApplyMove(move);

            // Check win for either player here if you can
            // For now, treat reaching no moves as "loss"
        }

        // Simplified: random rollout outcome
        return Random.value < 0.5f ? 1f : 0f;
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
            double uctScore = (child.Wins / (child.Visits + 1e-6)) +
                              Mathf.Sqrt(2f * Mathf.Log(node.Visits + 1) / (child.Visits + 1e-6f));

            if (uctScore > bestScore)
            {
                bestScore = uctScore;
                best = child;
            }
        }

        return best;
    }
}

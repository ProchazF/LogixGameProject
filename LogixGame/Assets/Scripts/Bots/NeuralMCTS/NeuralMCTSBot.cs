using System;
using System.Collections.Generic;
using UnityEngine;

public class NeuralMCTSBot
{
    private class Node
    {
        public GameBoard State;
        public Move Move;
        public Node Parent;

        public readonly List<Node> Children = new();

        // Player whose turn it is in this node's state:
        // 0 = player A
        // 1 = player B
        public int PlayerToMove;

        // Neural-network prior probability P(s, a).
        public float Prior;

        public int Visits;

        /*
         * Stored from the perspective of PlayerToMove in this node.
         *
         * Because a child has the opposite player to move, its value must
         * be negated when viewed from the parent.
         */
        public float ValueSum;

        public bool IsExpanded;

        public float MeanValue =>
            Visits > 0
                ? ValueSum / Visits
                : 0f;

        public Node(
            GameBoard state,
            Move move,
            Node parent,
            int playerToMove,
            float prior)
        {
            State = state;
            Move = move;
            Parent = parent;
            PlayerToMove = playerToMove;
            Prior = prior;
        }
    }

    private readonly LogixNeuralNetwork neuralNetwork;
    private readonly int iterations;
    private readonly float explorationConstant;

    public NeuralMCTSBot(
        LogixNeuralNetwork neuralNetwork,
        int iterations = 1000,
        float explorationConstant = 1.5f)
    {
        this.neuralNetwork = neuralNetwork != null
            ? neuralNetwork
            : throw new ArgumentNullException(nameof(neuralNetwork));

        if (iterations <= 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(iterations),
                "The number of MCTS iterations must be positive."
            );
        }

        this.iterations = iterations;
        this.explorationConstant = explorationConstant;
    }

    public Move GetBestMove(
        GameBoard rootBoard,
        WinShapeInstance[] playerACards,
        WinShapeInstance[] playerBCards,
        int currentPlayer)
    {
        if (rootBoard == null)
        {
            throw new ArgumentNullException(nameof(rootBoard));
        }

        if (!neuralNetwork.IsInitialized)
        {
            neuralNetwork.Initialize();
        }

        if (!neuralNetwork.IsInitialized)
        {
            Debug.LogError(
                "[NeuralMCTS] Neural network is not initialized."
            );

            return GetFallbackMove(rootBoard);
        }

        List<Move> rootLegalMoves = rootBoard.GetLegalMoves();

        if (rootLegalMoves.Count == 0)
        {
            return null;
        }

        // Immediately take a winning move if one already exists.
        Move immediateWin = FindImmediateWinningMove(
            rootBoard,
            rootLegalMoves,
            currentPlayer,
            playerACards,
            playerBCards
        );

        if (immediateWin != null)
        {
            Debug.Log(
                $"[NeuralMCTS] Immediate winning move found: " +
                $"{immediateWin}"
            );

            return immediateWin;
        }

        Node root = new Node(
            rootBoard.Clone(),
            null,
            null,
            currentPlayer,
            1f
        );

        for (int i = 0; i < iterations; i++)
        {
            Node leaf = SelectLeaf(root);

            float leafValue = ExpandAndEvaluate(
                leaf,
                playerACards,
                playerBCards
            );

            Backpropagate(leaf, leafValue);
        }

        Node bestChild = SelectMostVisitedChild(root);

        if (bestChild == null)
        {
            Debug.LogWarning(
                "[NeuralMCTS] Search generated no children. " +
                "Returning fallback move."
            );

            return rootLegalMoves[0];
        }

        Debug.Log(
            $"[NeuralMCTS] Selected {bestChild.Move}, " +
            $"visits={bestChild.Visits}, " +
            $"root score={-bestChild.MeanValue:F3}, " +
            $"prior={bestChild.Prior:F3}"
        );

        return bestChild.Move;
    }

    // ------------------------------------------------------------------
    // Selection
    // ------------------------------------------------------------------

    private Node SelectLeaf(Node node)
    {
        while (node.IsExpanded && node.Children.Count > 0)
        {
            node = SelectChildByPUCT(node);
        }

        return node;
    }

    private Node SelectChildByPUCT(Node parent)
    {
        Node bestChild = null;
        float bestScore = float.NegativeInfinity;

        float parentVisitsSqrt =
            Mathf.Sqrt(Mathf.Max(1, parent.Visits));

        foreach (Node child in parent.Children)
        {
            /*
             * child.MeanValue is from the child's PlayerToMove perspective.
             *
             * The parent represents the opposite player, so negate it to get
             * the value of this move from the parent's perspective.
             */
            float qValue =
                child.Visits > 0
                    ? -child.MeanValue
                    : 0f;

            float exploration =
                explorationConstant *
                child.Prior *
                parentVisitsSqrt /
                (1f + child.Visits);

            float score = qValue + exploration;

            if (score > bestScore)
            {
                bestScore = score;
                bestChild = child;
            }
        }

        return bestChild;
    }

    // ------------------------------------------------------------------
    // Expansion and neural evaluation
    // ------------------------------------------------------------------

    private float ExpandAndEvaluate(
        Node node,
        WinShapeInstance[] playerACards,
        WinShapeInstance[] playerBCards)
    {
        if (TryGetTerminalValue(
                node.State,
                node.PlayerToMove,
                playerACards,
                playerBCards,
                out float terminalValue))
        {
            return terminalValue;
        }

        List<Move> legalMoves = node.State.GetLegalMoves();

        if (legalMoves.Count == 0)
        {
            node.IsExpanded = true;
            return 0f;
        }

        EncodedLogixState encodedState =
            LogixStateEncoder.Encode(
                node.State,
                playerACards,
                playerBCards,
                node.PlayerToMove
            );

        NeuralNetworkResult networkResult =
            neuralNetwork.Evaluate(
                encodedState.BoardPlanes,
                encodedState.Features
            );

        float[] legalPriors = CalculateLegalMovePriors(
            legalMoves,
            networkResult.PolicyLogits
        );

        int nextPlayer = 1 - node.PlayerToMove;

        for (int i = 0; i < legalMoves.Count; i++)
        {
            Move move = legalMoves[i];

            GameBoard childState = node.State.Clone();
            childState.ApplyMove(move);

            Node child = new Node(
                childState,
                move,
                node,
                nextPlayer,
                legalPriors[i]
            );

            node.Children.Add(child);
        }

        node.IsExpanded = true;

        /*
         * The value output is assumed to evaluate the position from the
         * perspective of the current player encoded in the feature vector.
         */
        return Mathf.Clamp(networkResult.Value, -1f, 1f);
    }

    private static float[] CalculateLegalMovePriors(
        List<Move> legalMoves,
        float[] policyLogits)
    {
        if (policyLogits == null ||
            policyLogits.Length != LogixActionEncoder.ActionCount)
        {
            throw new ArgumentException(
                $"Expected {LogixActionEncoder.ActionCount} policy logits."
            );
        }

        float[] priors = new float[legalMoves.Count];

        float maximumLogit = float.NegativeInfinity;

        for (int i = 0; i < legalMoves.Count; i++)
        {
            int actionIndex =
                LogixActionEncoder.EncodeMove(legalMoves[i]);

            float logit = policyLogits[actionIndex];

            if (!float.IsNaN(logit) &&
                !float.IsInfinity(logit))
            {
                maximumLogit = Mathf.Max(
                    maximumLogit,
                    logit
                );
            }
        }

        // Invalid network output: use a uniform legal distribution.
        if (float.IsNegativeInfinity(maximumLogit))
        {
            SetUniformPriors(priors);
            return priors;
        }

        float sum = 0f;

        for (int i = 0; i < legalMoves.Count; i++)
        {
            int actionIndex =
                LogixActionEncoder.EncodeMove(legalMoves[i]);

            float logit = policyLogits[actionIndex];

            if (float.IsNaN(logit) ||
                float.IsInfinity(logit))
            {
                priors[i] = 0f;
                continue;
            }

            // Stable softmax over legal actions only.
            float probability =
                Mathf.Exp(logit - maximumLogit);

            priors[i] = probability;
            sum += probability;
        }

        if (sum <= 0f ||
            float.IsNaN(sum) ||
            float.IsInfinity(sum))
        {
            SetUniformPriors(priors);
            return priors;
        }

        for (int i = 0; i < priors.Length; i++)
        {
            priors[i] /= sum;
        }

        return priors;
    }

    private static void SetUniformPriors(float[] priors)
    {
        if (priors.Length == 0)
        {
            return;
        }

        float probability = 1f / priors.Length;

        for (int i = 0; i < priors.Length; i++)
        {
            priors[i] = probability;
        }
    }

    // ------------------------------------------------------------------
    // Backpropagation
    // ------------------------------------------------------------------

    private static void Backpropagate(
        Node node,
        float value)
    {
        /*
         * The leaf value is from the perspective of the player whose turn
         * it is at the leaf. Every parent represents the opposite player,
         * so the sign is reversed at each level.
         */
        while (node != null)
        {
            node.Visits++;
            node.ValueSum += value;

            value = -value;
            node = node.Parent;
        }
    }

    // ------------------------------------------------------------------
    // Terminal-state handling
    // ------------------------------------------------------------------

    private static bool TryGetTerminalValue(
        GameBoard board,
        int playerToMove,
        WinShapeInstance[] playerACards,
        WinShapeInstance[] playerBCards,
        out float value)
    {
        bool playerAWon = board.CheckWinFromBlack(
            playerACards,
            out _,
            out _
        );

        bool playerBWon = board.CheckWinFromBlack(
            playerBCards,
            out _,
            out _
        );

        if (!playerAWon && !playerBWon)
        {
            value = 0f;
            return false;
        }

        if (playerAWon && playerBWon)
        {
            value = 0f;
            return true;
        }

        int winner = playerAWon ? 0 : 1;

        value = winner == playerToMove
            ? 1f
            : -1f;

        return true;
    }

    private static Move FindImmediateWinningMove(
        GameBoard board,
        List<Move> legalMoves,
        int currentPlayer,
        WinShapeInstance[] playerACards,
        WinShapeInstance[] playerBCards)
    {
        WinShapeInstance[] currentPlayerCards =
            currentPlayer == 0
                ? playerACards
                : playerBCards;

        foreach (Move move in legalMoves)
        {
            GameBoard nextState = board.Clone();
            nextState.ApplyMove(move);

            if (nextState.CheckWinFromBlack(
                    currentPlayerCards,
                    out _,
                    out _))
            {
                return move;
            }
        }

        return null;
    }

    // ------------------------------------------------------------------
    // Final move choice
    // ------------------------------------------------------------------

    private static Node SelectMostVisitedChild(Node root)
    {
        Node bestChild = null;
        int bestVisits = -1;
        float bestValue = float.NegativeInfinity;

        foreach (Node child in root.Children)
        {
            // Convert the child's value to the root player's perspective.
            float rootValue = -child.MeanValue;

            Debug.Log(
                $"[NeuralMCTS] Move={child.Move}, " +
                $"visits={child.Visits}, " +
                $"value={rootValue:F3}, " +
                $"prior={child.Prior:F3}"
            );

            if (child.Visits > bestVisits ||
                (child.Visits == bestVisits &&
                 rootValue > bestValue))
            {
                bestVisits = child.Visits;
                bestValue = rootValue;
                bestChild = child;
            }
        }

        return bestChild;
    }

    private static Move GetFallbackMove(GameBoard board)
    {
        List<Move> legalMoves = board.GetLegalMoves();

        return legalMoves.Count > 0
            ? legalMoves[0]
            : null;
    }
}
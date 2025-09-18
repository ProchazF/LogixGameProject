using System.Collections.Generic;

public class MCTSNode
{
    public GameBoard State;
    public MCTSNode Parent;
    public List<MCTSNode> Children = new List<MCTSNode>();

    public Move Move; // move that led here
    public int Visits = 0;
    public float Wins = 0;

    public int Player; // whose turn this node is for

    private List<Move> untriedMoves;

    public MCTSNode(GameBoard state, int player, MCTSNode parent = null, Move move = null)
    {
        State = state;
        Parent = parent;
        Player = player;
        Move = move;
        untriedMoves = state.GetLegalMoves();
    }

    public bool IsFullyExpanded => untriedMoves.Count == 0;
    public bool IsLeaf => Children.Count == 0;

    public Move GetUntriedMove()
    {
        if (untriedMoves.Count == 0) return null;
        int idx = UnityEngine.Random.Range(0, untriedMoves.Count);
        Move m = untriedMoves[idx];
        untriedMoves.RemoveAt(idx);
        return m;
    }
}

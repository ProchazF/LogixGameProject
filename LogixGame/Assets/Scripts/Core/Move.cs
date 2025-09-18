using UnityEngine;

public enum MoveType
{
    Place,
    Move,
    Replace
}

public class Move
{
    public MoveType Type;
    public MarbleColor Color;
    public Vector2Int? From; // null if Place
    public Vector2Int To;

    public Move(MoveType type, MarbleColor color, Vector2Int? from, Vector2Int to)
    {
        Type = type;
        Color = color;
        From = from;
        To = to;
    }

    public override string ToString()
    {
        return Type switch
        {
            MoveType.Place => $"Place {Color} at {To}",
            MoveType.Move => $"Move {Color} from {From} to {To}",
            MoveType.Replace => $"Replace at {To} with {Color}",
            _ => "Unknown move"
        };
    }
}

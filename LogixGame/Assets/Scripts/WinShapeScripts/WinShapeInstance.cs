using UnityEngine;

public class WinShapeInstance
{
    public WinShape Shape;
    public MarbleColor AssignedColor;

    public string Name => Shape.Name;

    public WinShapeInstance(WinShape shape, MarbleColor color)
    {
        Shape = shape;
        AssignedColor = color;
    }
}

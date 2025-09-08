using System.Collections.Generic;
using System.Linq;
using UnityEngine;

public class WinShape
{
    public string Name;
    public Vector2Int[] Offsets;              // Original shape (5 points)
    public List<Vector2Int[]> Rotations;      // 4 rotations (0°, 90°, 180°, 270°)

    public WinShape(string name, Vector2Int[] shape)
    {
        Name = name;
        Offsets = shape;
        Rotations = GenerateRotations(shape);
    }

    private List<Vector2Int[]> GenerateRotations(Vector2Int[] shape)
    {
        var rotations = new List<Vector2Int[]>();
        var current = shape;
        for (int i = 0; i < 4; i++)
        {
            rotations.Add(Normalize(current));
            current = Rotate90(current);
        }
        return rotations;
    }

    private Vector2Int[] Rotate90(Vector2Int[] shape)
    {
        return shape.Select(v => new Vector2Int(-v.y, v.x)).ToArray();
    }

    private Vector2Int[] Normalize(Vector2Int[] shape)
    {
        int minX = shape.Min(v => v.x);
        int minY = shape.Min(v => v.y);
        return shape.Select(v => new Vector2Int(v.x - minX, v.y - minY)).ToArray();
    }
}
using System.Collections.Generic;
using UnityEngine;

public static class WinShapeDatabase
{
    public static List<WinShape> AllShapes = new List<WinShape>
    {
        new WinShape("Line", new[] {
            new Vector2Int(0,0), new Vector2Int(1,0), new Vector2Int(2,0), new Vector2Int(3,0), new Vector2Int(4,0)
        }),
        new WinShape("Plus", new[] {
            new Vector2Int(0,0), new Vector2Int(1,0), new Vector2Int(0,1), new Vector2Int(-1,0), new Vector2Int(0,-1)
        }),
        new WinShape("T-Shape", new[] {
            new Vector2Int(0,0), new Vector2Int(1,0), new Vector2Int(2,0), new Vector2Int(2,-1), new Vector2Int(2,1)
        }),
        new WinShape("Long L-Shape Mirrored", new[] {
            new Vector2Int(0,0), new Vector2Int(1,0), new Vector2Int(2,0), new Vector2Int(3,0), new Vector2Int(3,1)
        }),
        new WinShape("Long L-Shape", new[] {
            new Vector2Int(0,0), new Vector2Int(1,0), new Vector2Int(2,0), new Vector2Int(3,0), new Vector2Int(3,-1)
        }),
        new WinShape("Short L-Shape", new[] {
            new Vector2Int(0,0), new Vector2Int(1,0), new Vector2Int(2,0), new Vector2Int(2,1), new Vector2Int(2,2)
        }),
        new WinShape("Seven-Shape", new[] {
            new Vector2Int(0,0), new Vector2Int(1,0), new Vector2Int(2,0), new Vector2Int(2,-1), new Vector2Int(1,1)
        }),
        new WinShape("Mirrored Seven-Shape", new[] {
            new Vector2Int(0,0), new Vector2Int(1,0), new Vector2Int(2,0), new Vector2Int(1,-1), new Vector2Int(2,1)
        }),
        new WinShape("C-Shape", new[] {
            new Vector2Int(0,0), new Vector2Int(1,0), new Vector2Int(2,0), new Vector2Int(0,1), new Vector2Int(2,1)
        }),
        new WinShape("Stair-Shape", new[] {
            new Vector2Int(0,0), new Vector2Int(1,0), new Vector2Int(1,1), new Vector2Int(2,1), new Vector2Int(2,2)
        }),
        new WinShape("Z-Shape", new[] {
            new Vector2Int(0,0), new Vector2Int(1,0), new Vector2Int(2,0), new Vector2Int(2,-1), new Vector2Int(0,1)
        }),
        new WinShape("Reverse Z-Shape", new[] {
            new Vector2Int(0,0), new Vector2Int(1,0), new Vector2Int(2,0), new Vector2Int(2,1), new Vector2Int(0,-1)
        }),
        new WinShape("One-Shape", new[] { // 4 strainght with one sticking out in the middle (on the left on top)
            new Vector2Int(0,0), new Vector2Int(1,0), new Vector2Int(2,0), new Vector2Int(2,-1), new Vector2Int(3,0)
        }),
        new WinShape("Reverse One-Shape", new[] { // 4 strainght with one sticking out in the middle (on the right on top)
            new Vector2Int(0,0), new Vector2Int(1,0), new Vector2Int(2,0), new Vector2Int(2,1), new Vector2Int(3,0)
        }),
        new WinShape("b-shape", new[] { 
            new Vector2Int(0,0), new Vector2Int(1,0), new Vector2Int(2,0), new Vector2Int(0,1), new Vector2Int(1,1)
        }),
        new WinShape("d-shape", new[] {
            new Vector2Int(0,0), new Vector2Int(1,0), new Vector2Int(0,1), new Vector2Int(1,1), new Vector2Int(2,1)
        }),
        new WinShape("Snake", new[] { // 3 straight up connected to 2 straight up on the left
            new Vector2Int(0,0), new Vector2Int(1,0), new Vector2Int(2,0), new Vector2Int(2,-1), new Vector2Int(3,-1)
        }),
        new WinShape("Reverse Snake", new[] { // 3 straight up connected to 2 straight up on the right
            new Vector2Int(0,0), new Vector2Int(1,0), new Vector2Int(2,0), new Vector2Int(2,1), new Vector2Int(3,1)
        }),
    };
}

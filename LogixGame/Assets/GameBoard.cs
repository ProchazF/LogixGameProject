using UnityEngine;

public enum CellState { Empty, Player1, Player2 }

public class GameBoard : MonoBehaviour
{
    private CellState[,] board;

    public int width, height;

    public GameBoard(int w, int h)
    {
        width = w;
        height = h;
        board = new CellState[w, h];
    }

    public bool IsValidMove(int x, int y)
    {
        return x >= 0 && y >= 0 && x < width && y < height && board[x, y] == CellState.Empty;
    }

    public bool ApplyMove(int x, int y, CellState player)
    {
        if (!IsValidMove(x, y)) return false;
        board[x, y] = player;
        return true;
    }

    public CellState GetCell(int x, int y) => board[x, y];
}

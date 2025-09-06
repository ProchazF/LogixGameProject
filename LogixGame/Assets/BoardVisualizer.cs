using UnityEngine;

public class BoardVisualizer : MonoBehaviour
{
    public GameObject orbPrefab;
    public Transform[,] visualTiles;
    private GameBoard board;

    public void Init(GameBoard logicBoard)
    {
        board = logicBoard;
        visualTiles = new Transform[board.width, board.height];

        // spawn visual tiles or use existing ones
    }

    public void PlaceOrbVisual(int x, int y, Color color)
    {
        Vector3 pos = visualTiles[x, y].position;
        var orb = Instantiate(orbPrefab, pos, Quaternion.identity);
        orb.GetComponent<Renderer>().material.color = color;
    }
}

using UnityEngine;
using UnityEngine.UI;

public class BoardVisualizer : MonoBehaviour
{
    public GameObject tilePrefab;
    public GameBoard board;

    private RectTransform rectTransform;
    private GridLayoutGroup grid;

    void Awake()
    {
        rectTransform = GetComponent<RectTransform>();
        grid = GetComponent<GridLayoutGroup>();
    }

    public void Init(GameBoard gameBoard)
    {
        board = gameBoard;

        int cols = board.width;
        int rows = board.height;

        grid.constraintCount = cols;

        // Clear existing tiles if any
        foreach (Transform child in transform)
        {
            Destroy(child.gameObject);
        }

        // create tiles anmd assign them coordinates
        for (int y = board.height - 1; y >= 0; y--)  // Top to bottom
        {
            for (int x = 0; x < board.width; x++)
            {
                GameObject tile = Instantiate(tilePrefab, transform);

                BoardTile tileScript = tile.GetComponent<BoardTile>();
                if (tileScript != null)
                {
                    tileScript.Init(x, y, OnTileClicked);
                }
            }
        }
        ResizeGrid();
    }

    private void ResizeGrid()
    {
        if (transform.parent == null) return;

        RectTransform parentRect = transform.parent.GetComponent<RectTransform>();
        if (parentRect == null) return;

        if (grid == null)
        {
            Debug.LogWarning("GridLayoutGroup is not assigned!");
            return;
        }

        float canvasWidth = parentRect.rect.width;
        float canvasHeight = parentRect.rect.height;

        int cols = board.width;
        int rows = board.height;

        float cellSize = Mathf.Min(canvasWidth / cols, canvasHeight / rows);

        grid.cellSize = new Vector2(cellSize, cellSize);
    }

    private void OnTileClicked(int x, int y)
    {
        Debug.Log($"Tile clicked at ({x}, {y})");
        // TODO: Notify GameManager or handle move here
    }
}

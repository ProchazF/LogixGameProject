using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

public class BoardVisualizer : MonoBehaviour
{
    public GameObject tilePrefab;
    public GameBoard board;

    public System.Action<int, int> onTileClickedCallback;

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
                    tileScript.Init(x, y, (xPos, yPos) => onTileClickedCallback?.Invoke(xPos, yPos));
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

    //private void OnTileClicked(int x, int y)
    //{
    //    Debug.Log($"Tile clicked at ({x}, {y})");
    //    // TODO: Notify GameManager or handle move here
    //}



    // After every move you update the board
    public void Refresh()
    {
        int cols = board.width;
        int rows = board.height;

        int index = 0;
        for (int y = board.height - 1; y >= 0; y--)
        {
            for (int x = 0; x < board.width; x++)
            {
                if (index >= transform.childCount) return;

                Transform tileObj = transform.GetChild(index);
                BoardTile tile = tileObj.GetComponent<BoardTile>();
                if (tile != null)
                {
                    Vector2Int pos = new Vector2Int(x, y);

                    // If this tile is where the marble was picked up, show it as empty
                    if (GameManager.Instance != null && GameManager.Instance.IsPickedUpFrom(pos))
                    {
                        tile.UpdateMarble(MarbleColor.None);
                    }
                    else
                    {
                        MarbleColor c = board.GetMarble(x, y);
                        tile.UpdateMarble(c);
                    }
                }

                index++;
            }
        }
    }

    public void HighlightWin(List<Vector2Int> positions)
    {
        int cols = board.width;

        foreach (var pos in positions)
        {
            // Convert (x, y) into child index
            int index = (board.height - 1 - pos.y) * cols + pos.x;

            if (index >= 0 && index < transform.childCount)
            {
                var tileObj = transform.GetChild(index);
                var img = tileObj.GetComponent<Image>();
                if (img != null)
                    img.color = Color.yellow; // highlight
            }
        }
    }
}

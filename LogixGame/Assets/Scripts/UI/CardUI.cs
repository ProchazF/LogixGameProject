using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class CardUI : MonoBehaviour
{
    [SerializeField] private Transform shapeContainer;
    [SerializeField] private GameObject marblePrefab;
    [SerializeField] private TMP_Text shapeName;

    private float cellSize = 40f; // spacing between marbles

    public void Init(WinShapeInstance instance)
    {
        // Clear old marbles
        foreach (Transform child in shapeContainer)
            Destroy(child.gameObject);

        // Set name
        shapeName.text = instance.Name;

        // Pick color
        Color marbleColor = GetColor(instance.AssignedColor);

        // Get shape points
        var points = instance.Shape.Offsets;

        // Normalize to compact box
        int minX = int.MaxValue, minY = int.MaxValue;
        int maxX = int.MinValue, maxY = int.MinValue;
        foreach (var p in points)
        {
            if (p.x < minX) minX = p.x;
            if (p.y < minY) minY = p.y;
            if (p.x > maxX) maxX = p.x;
            if (p.y > maxY) maxY = p.y;
        }

        float width = (maxX - minX) * cellSize;
        float height = (maxY - minY) * cellSize;

        // Offset so shape is centered in container
        Vector2 offset = new Vector2(-width / 2f, -height / 2f);

        // Spawn marbles
        foreach (var p in points)
        {
            var go = Instantiate(marblePrefab, shapeContainer);
            var img = go.GetComponent<Image>();
            img.color = marbleColor;

            var rt = go.GetComponent<RectTransform>();
            rt.anchoredPosition = new Vector2((p.x - minX) * cellSize, (p.y - minY) * cellSize) + offset;
        }
    }

    private Color GetColor(MarbleColor c)
    {
        return c switch
        {
            MarbleColor.Red => Color.red,
            MarbleColor.Blue => Color.blue,
            MarbleColor.Green => Color.green,
            MarbleColor.Yellow => Color.yellow,
            _ => Color.gray
        };
    }
}

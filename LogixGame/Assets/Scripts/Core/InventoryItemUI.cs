using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class InventoryItemUI : MonoBehaviour
{
    public MarbleColor color;
    public TextMeshProUGUI countText;

    public Image marbleImage;

    private Button button;

    void Awake()
    {
        button = GetComponent<Button>();
        if (button != null)
        {
            button.onClick.AddListener(OnClicked);
        }
    }

    public void Set(MarbleColor color, int count)
    {
        this.color = color;

        if (countText != null)
            countText.text = $"x{count}";

        if (marbleImage != null)
            marbleImage.color = GetUnityColor(color);
    }

    private Color GetUnityColor(MarbleColor color)
    {
        return color switch
        {
            MarbleColor.Red => Color.red,
            MarbleColor.Blue => Color.blue,
            MarbleColor.Green => Color.green,
            MarbleColor.Yellow => Color.yellow,
            MarbleColor.Grey => Color.grey,
            MarbleColor.Black => Color.black,
            _ => Color.white,
        };
    }

    private void OnClicked()
    {
       // Debug.Log($"Marble clicked: {color}");
        GameManager.Instance?.OnMarbleSelected(color);
    }

}
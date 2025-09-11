using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class InventorySlot : MonoBehaviour
{
    public Image marbleImage;
    public TextMeshProUGUI countText;

    public void SetColor(MarbleColor color)
    {
        marbleImage.color = color switch
        {
            MarbleColor.Red => Color.red,
            MarbleColor.Blue => Color.blue,
            MarbleColor.Green => Color.green,
            MarbleColor.Yellow => Color.yellow,
            MarbleColor.Grey => Color.gray,
            _ => Color.clear
        };
    }

    public void SetCount(int count)
    {
        countText.text = "x" + count;
    }
}

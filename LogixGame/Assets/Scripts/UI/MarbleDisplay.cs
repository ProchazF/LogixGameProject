using UnityEngine;
using UnityEngine.UI;

public class MarbleDisplay : MonoBehaviour
{
    public Image marbleImage;

    public void SetColor(MarbleColor color)
    {
        marbleImage.color = MarbleColorToUnityColor(color);
    }

    private Color MarbleColorToUnityColor(MarbleColor color)
    {
        return color switch
        {
            MarbleColor.Red => Color.red,
            MarbleColor.Blue => Color.blue,
            MarbleColor.Green => Color.green,
            MarbleColor.Yellow => Color.yellow,
            MarbleColor.Grey => Color.gray,
            MarbleColor.Black => Color.black,
            _ => Color.clear,
        };
    }
}
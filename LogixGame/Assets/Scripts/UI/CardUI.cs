using TMPro;
using UnityEngine;
using UnityEngine.UI;

public class CardUI : MonoBehaviour
{
    public TextMeshProUGUI nameText;
    public Image colorCircle;

    public void Init(string shapeName, MarbleColor blockedColor)
    {
        Debug.Log($"Initializing card: {shapeName} with color {blockedColor}");

        nameText.text = shapeName;
        colorCircle.color = MarbleColorUtils.ToColor(blockedColor); // Add helper if needed
    }

    public static class MarbleColorUtils
    {
        public static Color ToColor(MarbleColor color)
        {
            return color switch
            {
                MarbleColor.Red => Color.red,
                MarbleColor.Blue => Color.blue,
                MarbleColor.Green => Color.green,
                MarbleColor.Yellow => Color.yellow,
                MarbleColor.Grey => Color.grey,
                MarbleColor.Black => Color.black,
                _ => Color.white
            };
        }
    }
}

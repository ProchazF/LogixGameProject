using UnityEngine;
using UnityEngine.UI;

public class BoardTile : MonoBehaviour
{
    public int x, y; // Pozice na desce
    private Button button;
    private Image marbleImage;

    public void Init(int x, int y, System.Action<int, int> onClick)
    {
        this.x = x;
        this.y = y;

        button = GetComponent<Button>();
        if (button != null)
        {
            button.onClick.RemoveAllListeners();
            button.onClick.AddListener(() => onClick?.Invoke(x, y));
        }

        // Najdeme child objekt s Image komponentou
        Transform child = transform.Find("MarbleVisual");
        if (child != null)
            marbleImage = child.GetComponent<Image>();
    }

    public void UpdateMarble(MarbleColor color)
    {
        if (marbleImage == null) return;

        switch (color)
        {
            case MarbleColor.Red: marbleImage.color = Color.red; break;
            case MarbleColor.Blue: marbleImage.color = Color.blue; break;
            case MarbleColor.Green: marbleImage.color = Color.green; break;
            case MarbleColor.Yellow: marbleImage.color = Color.yellow; break;
            case MarbleColor.Grey: marbleImage.color = Color.gray; break;
            case MarbleColor.Black: marbleImage.color = Color.black; break;
            default:
                marbleImage.color = new Color(1, 1, 1, 0); // Prùhledná
                break;
        }
    }
}

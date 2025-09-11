using UnityEngine;
using UnityEngine.UI;
using UnityEngine.InputSystem;

public class CursorMarble : MonoBehaviour
{
    public Image marbleImage;
    public Canvas canvas;

    private MarbleColor currentColor = MarbleColor.None;

    void Update()
    {
        if (canvas.renderMode == RenderMode.ScreenSpaceOverlay)
        {
            Vector2 mousePos = Mouse.current.position.ReadValue();
            transform.position = mousePos;
        }
        else
        {
            Vector2 mousePos = Mouse.current.position.ReadValue();
            Vector2 uiPos;

            RectTransformUtility.ScreenPointToLocalPointInRectangle(
                canvas.transform as RectTransform,
                mousePos,
                canvas.worldCamera,
                out uiPos
            );

            (transform as RectTransform).anchoredPosition = uiPos;
        }
    }

    public void SetColor(MarbleColor color)
    {
        currentColor = color;
        marbleImage.enabled = true;
        marbleImage.color = GetColor(color);
    }

    public void Clear()
    {
        currentColor = MarbleColor.None;
        marbleImage.enabled = false;
    }

    private Color GetColor(MarbleColor color)
    {
        return color switch
        {
            MarbleColor.Red => Color.red,
            MarbleColor.Blue => Color.blue,
            MarbleColor.Green => Color.green,
            MarbleColor.Yellow => Color.yellow,
            MarbleColor.Grey => Color.gray,
            MarbleColor.Black => Color.black,
            _ => new Color(0, 0, 0, 0)
        };
    }
}

using UnityEngine;
using UnityEngine.UI;

public class BoardTile : MonoBehaviour
{
    public int x, y; // Grid coordinates
    private Button button;

    public void Init(int x, int y, System.Action<int, int> onClick)
    {
        this.x = x;
        this.y = y;

        button = GetComponent<Button>();
        if (button != null)
        {
            button.onClick.AddListener(() => onClick?.Invoke(x, y));
        }
    }
}

using UnityEngine;
using System.Collections.Generic;

public class InventoryUI : MonoBehaviour
{
    public GameObject itemPrefab; // InventoryItemUI prefab
    public Transform container;   // Where to spawn items

    private Dictionary<MarbleColor, InventoryItemUI> slots = new();

    public void Init(Dictionary<MarbleColor, int> inventory)
    {
        // Clear old
        foreach (Transform child in container)
            Destroy(child.gameObject);

        slots.Clear();

        foreach (var entry in inventory)
        {
            var go = Instantiate(itemPrefab, container);
            var itemUI = go.GetComponent<InventoryItemUI>();
            if (itemUI != null)
            {
                itemUI.Set(entry.Key, entry.Value);
                slots[entry.Key] = itemUI;
            }

            Debug.Log($"Created inventory item: {entry.Key} x{entry.Value}");
        }
    }

    public void UpdateCount(MarbleColor color, int count)
    {
        if (slots.TryGetValue(color, out var itemUI))
        {
            itemUI.Set(color, count);
        }
    }
}
using UnityEngine;
using UnityEngine.UI;
using TMPro;
using System.Collections.Generic;

public class InventoryUI : MonoBehaviour
{
    public GameObject itemPrefab; // The InventoryItem prefab
    public Transform container;   // Where to spawn items (InventoryPanel)

    private Dictionary<MarbleColor, InventorySlot> slots = new();

    public void Init(Dictionary<MarbleColor, int> inventory)
    {
        foreach (Transform child in container)
            Destroy(child.gameObject);

        foreach (var entry in inventory)
        {
            var item = Instantiate(itemPrefab, container);
            var slot = item.GetComponent<InventorySlot>();
            slot.SetColor(entry.Key);
            slot.SetCount(entry.Value);
            slots[entry.Key] = slot;
            Debug.Log($"Creating inventory item: {entry.Key} x{entry.Value}");
        }
    }

    public void UpdateCount(MarbleColor color, int count)
    {
        if (slots.TryGetValue(color, out var slot))
        {
            slot.SetCount(count);
        }
    }
}

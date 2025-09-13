using System.Collections.Generic;
using UnityEngine;

public class IllegalMarblesUI : MonoBehaviour
{
    public GameObject marbleDisplayPrefab; // Assign your MarbleDisplay prefab here
    public Transform container; // The UI panel (e.g., HorizontalLayoutGroup above inventory)

    private readonly List<GameObject> marbleInstances = new();

    public void SetIllegalMarbles(List<MarbleColor> colors)
    {
        // Clear previous marbles
        foreach (var go in marbleInstances)
            Destroy(go);
        marbleInstances.Clear();

        // Create new visuals
        foreach (var color in colors)
        {
            var instance = Instantiate(marbleDisplayPrefab, container);
            var display = instance.GetComponent<MarbleDisplay>();
            if (display != null)
                display.SetColor(color);

            marbleInstances.Add(instance);
        }
    }
}

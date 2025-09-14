using UnityEngine;

public class PlayerCardUI : MonoBehaviour
{
    public GameObject cardPrefab;

    [SerializeField] private Transform cardContainer;  // assign this to PlayerA or PlayerB container in Inspector

    public void ShowCards(WinShapeInstance[] cards)
    {
        // Clear old cards
        foreach (Transform child in cardContainer)
            Destroy(child.gameObject);

        // Instantiate new cards
        foreach (var card in cards)
        {
            var go = Instantiate(cardPrefab, cardContainer);
            var ui = go.GetComponent<CardUI>();
            if (ui != null)
                ui.Init(card.Name, card.AssignedColor);
        }
    }
}


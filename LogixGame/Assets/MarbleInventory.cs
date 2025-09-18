using System.Collections.Generic;
using UnityEngine;

public class MarbleInventory
{
    private Dictionary<MarbleColor, int> counts;

    public MarbleInventory()
    {
        counts = new Dictionary<MarbleColor, int>
        {
            { MarbleColor.Red, 6 },
            { MarbleColor.Blue, 6 },
            { MarbleColor.Green, 6 },
            { MarbleColor.Yellow, 6 },
            { MarbleColor.Grey, 2 }
        };
    }

    public bool Has(MarbleColor color)
    {
        return counts.ContainsKey(color) && counts[color] > 0;
    }

    // Use the color marble
    public bool Use(MarbleColor color)
    {
        if (!Has(color)) return false;
        counts[color]--;
        return true;
    }

    // When replacing you add one back
    public void AddBack(MarbleColor color)
    {
        if (!counts.ContainsKey(color)) return;
        counts[color]++;
    }

    public int GetCount(MarbleColor color)
    {
        return counts.ContainsKey(color) ? counts[color] : 0;
    }

    public MarbleInventory Clone()
    {
        var copy = new MarbleInventory();
        foreach (var kv in counts) // whatever dictionary/list you store counts in
        {
            copy.counts[kv.Key] = kv.Value;
        }
        return copy;
    }

    public Dictionary<MarbleColor, int> GetAllCounts()
    {
        return new Dictionary<MarbleColor, int>(counts);
    }
}

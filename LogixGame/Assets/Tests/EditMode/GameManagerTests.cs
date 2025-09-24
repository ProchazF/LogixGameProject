using NUnit.Framework;
using UnityEngine;
using TMPro;
using System.Reflection;

public class GameManager_EditModeTests
{
    private GameManager CreateGameManager()
    {
        var go = new GameObject("GM_Test");
        var gm = go.AddComponent<GameManager>();

        // Assign dummy UI so we don’t get NullReferenceExceptions
        var turnGO = new GameObject("TurnText");
        gm.GetType()
          .GetField("turnText", BindingFlags.NonPublic | BindingFlags.Instance)
          ?.SetValue(gm, turnGO.AddComponent<TextMeshProUGUI>());

        return gm;
    }

    // ---------- Parse helpers ----------

    [Test]
    public void ParseMode_ValidStrings_ReturnsCorrectEnum()
    {
        var gm = CreateGameManager();

        Assert.AreEqual(GameMode.PvP, InvokePrivateParseMode(gm, "PvP"));
        Assert.AreEqual(GameMode.PvE, InvokePrivateParseMode(gm, "PvE"));
        Assert.AreEqual(GameMode.EvE, InvokePrivateParseMode(gm, "EvE"));
    }

    [Test]
    public void ParseDifficulty_ValidStrings_ReturnsCorrectEnum()
    {
        var gm = CreateGameManager();

        Assert.AreEqual(Difficulty.Easy, InvokePrivateParseDifficulty(gm, "Easy"));
        Assert.AreEqual(Difficulty.Normal, InvokePrivateParseDifficulty(gm, "Normal"));
        Assert.AreEqual(Difficulty.Hard, InvokePrivateParseDifficulty(gm, "Hard"));
    }

    // ---------- Card generation ----------

    [Test]
    public void GeneratePlayerCards_ReturnsTwoUniqueCards()
    {
        var gm = CreateGameManager();
        var cards = InvokePrivateGenerateCards(gm);

        Assert.AreEqual(2, cards.Length, "Should always generate 2 cards");
        Assert.AreNotEqual(cards[0].Shape, cards[1].Shape, "Cards must be unique shapes");
    }

    // ---------- Bot turn logic ----------

    [Test]
    public void IsBotsTurn_ReturnsTrue_ForCorrectModes()
    {
        var gm = CreateGameManager();

        // PvP: never bot’s turn
        SetPrivateField(gm, "mode", GameMode.PvP);
        SetPrivateField(gm, "currentPlayer", 0);
        Assert.IsFalse(InvokePrivateIsBotsTurn(gm));

        // PvE: bot is always Player 2 (index 1)
        SetPrivateField(gm, "mode", GameMode.PvE);
        SetPrivateField(gm, "currentPlayer", 1);
        Assert.IsTrue(InvokePrivateIsBotsTurn(gm));

        // EvE: always bots
        SetPrivateField(gm, "mode", GameMode.EvE);
        SetPrivateField(gm, "currentPlayer", 0);
        Assert.IsTrue(InvokePrivateIsBotsTurn(gm));
    }

    // ---------- Helpers for reflection ----------

    private GameMode InvokePrivateParseMode(GameManager gm, string input)
    {
        var method = typeof(GameManager).GetMethod("ParseMode",
            BindingFlags.NonPublic | BindingFlags.Instance);
        return (GameMode)method.Invoke(gm, new object[] { input });
    }

    private Difficulty InvokePrivateParseDifficulty(GameManager gm, string input)
    {
        var method = typeof(GameManager).GetMethod("ParseDifficulty",
            BindingFlags.NonPublic | BindingFlags.Instance);
        return (Difficulty)method.Invoke(gm, new object[] { input });
    }

    private WinShapeInstance[] InvokePrivateGenerateCards(GameManager gm)
    {
        var method = typeof(GameManager).GetMethod("GeneratePlayerCards",
            BindingFlags.NonPublic | BindingFlags.Instance);
        return (WinShapeInstance[])method.Invoke(gm, new object[] { null });
    }

    private bool InvokePrivateIsBotsTurn(GameManager gm)
    {
        var method = typeof(GameManager).GetMethod("IsBotsTurn",
            BindingFlags.NonPublic | BindingFlags.Instance);
        return (bool)method.Invoke(gm, null);
    }

    private void InvokePrivateUpdateTurnText(GameManager gm)
    {
        var method = typeof(GameManager).GetMethod("UpdateTurnText",
            BindingFlags.NonPublic | BindingFlags.Instance);
        method.Invoke(gm, null);
    }

    private void SetPrivateField(GameManager gm, string fieldName, object value)
    {
        var field = typeof(GameManager).GetField(fieldName,
            BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Public);
        field.SetValue(gm, value);
    }
}

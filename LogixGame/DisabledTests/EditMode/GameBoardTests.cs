using NUnit.Framework;
using System.Collections.Generic;
using UnityEngine;

public class GameBoard_EditModeTests
{
    private GameBoard board;

    [SetUp]
    public void SetUp()
    {
        board = new GameBoard(7, 7); // standard board
    }

    [Test]
    public void InitializeBoard_PlacesBlackInCenter()
    {
        int cx = board.width / 2;
        int cy = board.height / 2;

        Assert.AreEqual(MarbleColor.Black, board.GetMarble(cx, cy));
    }

    [Test]
    public void PlaceMarble_FailsIfNotAdjacent()
    {
        // top-left corner has no adjacent marbles at start
        bool placed = board.PlaceMarble(0, 0, MarbleColor.Red);
        Assert.IsFalse(placed);
        Assert.AreEqual(MarbleColor.None, board.GetMarble(0, 0));
    }

    [Test]
    public void PlaceMarble_SucceedsNextToBlack()
    {
        int cx = board.width / 2;
        int cy = board.height / 2;

        // Adjacent to black in center
        bool placed = board.PlaceMarble(cx + 1, cy, MarbleColor.Red);
        Assert.IsTrue(placed);
        Assert.AreEqual(MarbleColor.Red, board.GetMarble(cx + 1, cy));
    }

    [Test]
    public void PlaceMarble_FailsIfColorWasUsedLastTurn()
    {
        int cx = board.width / 2;
        int cy = board.height / 2;

        board.RecordMoveColors(MarbleColor.Red); // mark red as banned
        bool placed = board.PlaceMarble(cx + 1, cy, MarbleColor.Red);
        Assert.IsFalse(placed);
    }

    [Test]
    public void MoveMarble_Fails_WhenDestNotAdjacentToAnyMarble()
    {
        int cx = board.width / 2;
        int cy = board.height / 2;

        board.SetMarble(cx + 1, cy, MarbleColor.Red);
        board.RecordMoveColors(MarbleColor.Blue); // allow Red this turn

        // (cx+2,cy) is NOT adjacent to Black or any other marble in this setup
        bool moved = board.MoveMarble(cx + 1, cy, cx + 2, cy);

        Assert.IsFalse(moved);
        Assert.AreEqual(MarbleColor.Red, board.GetMarble(cx + 1, cy));
        Assert.AreEqual(MarbleColor.None, board.GetMarble(cx + 2, cy));
    }

    [Test]
    public void MoveMarble_Fails_WhenReusingLastMoveColor()
    {
        int cx = board.width / 2;
        int cy = board.height / 2;

        // Setup a Red on board
        board.SetMarble(cx + 1, cy, MarbleColor.Red);

        // Last move used Red → Red is banned this turn
        board.RecordMoveColors(MarbleColor.Red);

        bool moved = board.MoveMarble(cx + 1, cy, cx, cy + 1);

        Assert.IsFalse(moved);
    }

    [Test]
    public void MoveMarble_Fails_WhenSourceIsBlocked()
    {
        int cx = board.width / 2;
        int cy = board.height / 2;

        board.SetMarble(cx + 1, cy, MarbleColor.Red);

        // Block all four orthogonal neighbors around (cx+1,cy)
        board.SetMarble(cx + 2, cy, MarbleColor.Blue);
        board.SetMarble(cx + 1, cy + 1, MarbleColor.Blue);
        board.SetMarble(cx + 1, cy - 1, MarbleColor.Blue);
        // Left neighbor is the Black at (cx,cy) already occupied

        board.RecordMoveColors(MarbleColor.Blue); // allow Red this turn

        Assert.IsTrue(board.IsBlocked(cx + 1, cy));
        Assert.IsFalse(board.MoveMarble(cx + 1, cy, cx, cy + 1));
    }

    [Test]
    public void MoveMarble_SucceedsWithValidPath()
    {
        int cx = board.width / 2;
        int cy = board.height / 2;

        board.PlaceMarble(cx + 1, cy, MarbleColor.Red);
        board.PlaceMarble(cx + 2, cy, MarbleColor.Blue);
        bool moved = board.MoveMarble(cx + 1, cy, cx - 1, cy); // move to the other side of black marble
        Assert.IsTrue(moved);
        Assert.AreEqual(MarbleColor.Red, board.GetMarble(cx - 1, cy));
        Assert.AreEqual(MarbleColor.None, board.GetMarble(cx + 1, cy));
    }

    [Test]
    public void MoveMarble_FailsIfDestinationOccupied()
    {
        int cx = board.width / 2;
        int cy = board.height / 2;

        board.PlaceMarble(cx + 1, cy, MarbleColor.Red);
        board.PlaceMarble(cx + 2, cy, MarbleColor.Blue);

        bool moved = board.MoveMarble(cx + 1, cy, cx + 2, cy);
        Assert.IsFalse(moved);
    }

    [Test]
    public void ReplaceMarble_SucceedsAndUpdatesInventory()
    {
        int cx = board.width / 2;
        int cy = board.height / 2;

        board.PlaceMarble(cx + 1, cy, MarbleColor.Red);
        board.PlaceMarble(cx + 2, cy, MarbleColor.Green);

        bool replaced = board.ReplaceMarble(cx + 1, cy, MarbleColor.Blue);
        Assert.IsTrue(replaced);
        Assert.AreEqual(MarbleColor.Blue, board.GetMarble(cx + 1, cy));

        // Red should be returned to inventory
        var inv = board.GetInventory();
        Assert.Greater(inv[MarbleColor.Red], 0);
    }

    [Test]
    public void ReplaceMarble_FailsOnBlack()
    {
        int cx = board.width / 2;
        int cy = board.height / 2;

        bool replaced = board.ReplaceMarble(cx, cy, MarbleColor.Blue);
        Assert.IsFalse(replaced);
        Assert.AreEqual(MarbleColor.Black, board.GetMarble(cx, cy));
    }

    [Test]
    public void IsBlocked_ReturnsTrue_WhenSurrounded()
    {
        int cx = board.width / 2;
        int cy = board.height / 2;

        // Surround black marble with others
        board.PlaceMarble(cx + 1, cy, MarbleColor.Red);
        board.PlaceMarble(cx - 1, cy, MarbleColor.Blue);
        board.PlaceMarble(cx, cy + 1, MarbleColor.Green);
        board.PlaceMarble(cx, cy - 1, MarbleColor.Yellow);

        Assert.IsTrue(board.IsBlocked(cx, cy));
    }

    [Test]
    public void Clone_CreatesIndependentCopy()
    {
        int cx = board.width / 2;
        int cy = board.height / 2;

        board.PlaceMarble(cx + 1, cy, MarbleColor.Red);
        var clone = board.Clone();

        Assert.AreEqual(MarbleColor.Red, clone.GetMarble(cx + 1, cy));

        // Changing clone doesn’t affect original
        clone.SetMarble(cx + 1, cy, MarbleColor.Blue);
        Assert.AreEqual(MarbleColor.Red, board.GetMarble(cx + 1, cy));
        Assert.AreEqual(MarbleColor.Blue, clone.GetMarble(cx + 1, cy));
    }

    [Test]
    public void GetLegalMoves_ContainsPlacementNextToBlack()
    {
        int cx = board.width / 2;
        int cy = board.height / 2;

        var moves = board.GetLegalMoves();
        Assert.IsTrue(moves.Exists(m => m.Type == MoveType.Place && m.To == new Vector2Int(cx + 1, cy)));
    }
}

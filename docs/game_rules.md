# Logix Game Rules

[← Back to main repository](../README.md)

## Overview

Logix is a deterministic two-player board game played on a `7 × 7` board.

Players take turns placing, moving, or replacing coloured marbles. The goal is to form one of the player's assigned five-cell objective shapes using a valid colour combination that includes the central black marble.

## Board

The game is played on a square board with seven rows and seven columns.

```text
7 rows × 7 columns
```

At the beginning of the game, a single black marble is placed in the centre of the board.

```text
. . . . . . .
. . . . . . .
. . . . . . .
. . . K . . .
. . . . . . .
. . . . . . .
. . . . . . .
```

`K` represents the black marble.

## Marble Colours

The game uses the following marble colours:

- red,
- green,
- blue,
- yellow,
- grey,
- black.

The standard coloured marbles are red, green, blue, and yellow.

Grey marbles act as wildcards when validating a winning shape.

The black marble is unique and begins in the centre of the board.

## Inventory

The coloured marbles are taken from a shared inventory.

Placing or replacing a marble consumes the selected marble from the inventory.

Moving an existing marble does not consume a new marble.

When a marble is removed from the board as part of a replacement, the environment updates the inventory according to the implemented replacement rules.

## Players and Turns

The game is played by two players.

Players alternate turns. During a turn, the current player selects exactly one legal action.

A legal turn may contain one of the following action types:

1. placement,
2. movement,
3. replacement.

After the action is executed, the game checks whether the active player has created a valid winning shape.

If no player has won, control passes to the other player.

## Placement

A placement action adds a marble from the shared inventory to an empty board cell.

A placement is legal only when:

- the selected colour is available in the inventory,
- the selected colour is not currently forbidden,
- the destination cell is empty,
- the destination is orthogonally adjacent to at least one occupied cell.

Orthogonal adjacency means sharing an edge:

```text
    X
  X C X
    X
```

Diagonal contact alone is not sufficient.

## Movement

A movement action relocates a marble already present on the board.

Both coloured marbles and the black marble may be movable, provided that the move satisfies the movement rules.

A movement is legal only when:

- the selected source contains a movable marble,
- the source marble is not completely blocked,
- the destination cell is empty,
- the destination is reachable through empty orthogonally connected cells,
- the destination is adjacent to the occupied structure after accounting for the removed source marble,
- moving the marble does not create an invalid disconnected or floating placement.

The original source position is treated as empty when validating the destination.

Movement uses four-directional connectivity. Diagonal movement through cells is not allowed.

## Replacement

A replacement action replaces a marble already present on the board with a marble of another colour from the shared inventory.

A replacement is legal only when:

- the target marble may legally be replaced,
- the replacement colour is available,
- the replacement colour is not currently forbidden,
- the move satisfies all additional colour and inventory restrictions.

After a replacement, both colours involved in the action become relevant to the next-turn colour restriction.

## Forbidden Colours

The colour or colours used in the previous move are temporarily forbidden for the next player.

This prevents the next player from immediately using the same colour combination.

The exact set depends on the previous action:

- placement uses one colour,
- movement uses the moved marble's colour,
- replacement involves both the removed colour and the inserted colour.

Grey may also become forbidden when it is involved in an action.

The forbidden set is updated after every completed move.

## Objective Cards

Each player receives two objective cards.

Each card represents a five-cell shape. A player wins by forming a board configuration matching at least one of their objective cards.

Objective shapes may be rotated.

Mirrored variants are not automatically accepted unless the mirrored shape exists as a separate objective definition.

Examples of objective categories used by the project include:

- line,
- plus,
- T shape,
- long L,
- reverse Z,
- short L,
- snake-like shapes,
- other five-cell configurations.

The authoritative shape definitions are stored in the game implementation.

## Winning Shape

A winning shape consists of exactly five cells matching one of the active player's objective cards.

A valid winning shape must satisfy all of the following conditions:

- it matches one of the player's assigned objective shapes,
- rotations are allowed,
- mirroring is not allowed unless represented by a separate shape,
- the black marble is part of the shape,
- all non-grey and non-black marbles use one consistent colour,
- grey marbles may substitute for the selected colour,
- the shape does not use the colour blocked by the objective card,
- the connected component of the selected colour contains exactly the required five cells.

## Colour Consistency

A valid shape is based on one standard colour:

- red,
- green,
- blue, or
- yellow.

The five shape cells may contain:

- the selected standard colour,
- the black marble,
- grey wildcard marbles.

Other standard colours invalidate the shape.

For example, a red winning shape may contain red, grey, and black marbles, but it may not contain green, blue, or yellow marbles.

## Grey Marbles

Grey marbles act as wildcards during shape validation.

A grey marble may represent the standard colour used by the candidate winning shape.

Grey marbles do not force the candidate shape to use any particular colour.

A shape containing grey marbles must still satisfy every other winning condition, including the required objective geometry and inclusion of the black marble.

## Black Marble

The black marble is unique.

It starts in the centre of the board and must be included in every valid winning shape.

The black marble may participate with any standard colour and may be moved when the movement rules allow it.

It does not behave as a standard inventory colour.

## Blocked Card Colour

An objective card may specify a blocked colour.

A player cannot complete that card using the blocked colour as the main colour of the winning shape.

Grey and black marbles remain usable, but the consistent standard colour chosen for the shape cannot be the card's blocked colour.

## Exact Five-Marble Requirement

The winning shape must contain exactly five connected relevant marbles.

A candidate shape is invalid when additional marbles of the same main colour are orthogonally connected to the shape and extend the corresponding connected component beyond the required five cells.

This rule prevents a valid objective from being counted merely as a subset of a larger same-colour structure.

Grey marbles connected nearby do not automatically invalidate the shape unless they are included in the evaluated component according to the implementation's shape-validation logic.

## End of the Game

The game ends when:

- one player creates a valid winning shape, or
- the configured maximum number of turns is reached.

In training or tournament environments, reaching the maximum game length may be treated as a draw.

Typical result values in the Python environment are:

```text
+1  first player wins
 0  draw or unfinished maximum-length game
-1  second player wins
```

The exact interpretation may depend on whether the result is stored globally or from the current player's perspective.

## Illegal Actions

An action is illegal when it violates any board, inventory, connectivity, colour, or turn rule.

The user interface should prevent human players from executing illegal actions.

AI agents are expected to choose from the environment's generated legal-move list.

Experiment scripts may replace an illegal bot move with a legal fallback move to prevent an entire tournament from terminating, while also reporting the error for debugging.

## Rule Consistency Between Implementations

The game rules are implemented independently in:

- the Unity project,
- the Python training environment.

Both implementations must remain consistent, especially for:

- move legality,
- inventory changes,
- forbidden colours,
- objective transformations,
- shape validation,
- win detection.

When changing a rule, corresponding tests and documentation should be updated in both components.
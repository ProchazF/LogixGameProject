# State and Action Encoding

[← Back to EvaluationFunction](../../EvaluationFunction/README.md)

## Overview

The game environment represents Logix states and moves using symbolic Python structures. The neural network, however, requires numerical inputs and outputs with fixed dimensions.

The encoding layer therefore provides the interface between:

- the Logix game environment,
- Monte Carlo Tree Search,
- the replay buffer,
- the neural network,
- model inference,
- ONNX export.

Two modules are responsible for this conversion:

| Module | Responsibility |
|---|---|
| `state_encoding.py` | Converts complete game states into neural-network inputs. |
| `action_encoding.py` | Maps symbolic game moves to fixed policy-output indices and back. |

The current implementation uses:

```text
Board tensor shape:     (6, 7, 7)
Feature-vector length:  99
Action-space size:      2891
```

These dimensions form a shared interface between the environment, network, search algorithm, checkpoints, and exported ONNX model.

---

# State Encoding

## Purpose

The state encoder transforms a complete Logix position into two numerical inputs:

1. a spatial board tensor,
2. a non-spatial feature vector.

```text
LogixState
    │
    ├── board information
    │        │
    │        ▼
    │   (6, 7, 7) tensor
    │
    └── additional state information
             │
             ▼
        99-value vector
```

The board tensor is processed by the convolutional part of the network. The feature vector represents information that does not naturally belong to individual board cells.

---

## State Snapshot

The encoder works with a stable state snapshot rather than depending directly on a mutable graphical or live environment.

A snapshot contains the information required to evaluate the position:

- board contents,
- black-marble position,
- current player,
- turn number,
- forbidden colours,
- shared inventory,
- player objective cards.

A simplified conceptual representation is:

```python
LogixState(
    board=...,
    player=...,
    turn=...,
    banned=...,
    inventory=...,
    objectives=...,
)
```

Snapshots must remain unchanged after they are stored in the replay buffer. For this reason, mutable environment data should be copied when a snapshot is created.

---

## Board Tensor

The Logix board has dimensions:

```text
7 × 7
```

The board is encoded using six binary feature planes, one for each marble category.

| Plane | Marble type |
|---:|---|
| `0` | Red |
| `1` | Green |
| `2` | Blue |
| `3` | Yellow |
| `4` | Grey |
| `5` | Black |

Each plane has shape:

```text
(7, 7)
```

The complete board tensor therefore has shape:

```text
(6, 7, 7)
```

For each board coordinate, the corresponding cell in a plane is:

```text
1  if the associated marble occupies the cell
0  otherwise
```

For example, a red marble at row `2`, column `4` produces:

```python
board_planes[0, 2, 4] = 1
```

A black marble at the centre produces:

```python
board_planes[5, 3, 3] = 1
```

All other planes contain zero at that coordinate.

---

## Board Codes

The symbolic environment uses integer codes for standard marble colours.

| Code | Meaning |
|---:|---|
| `0` | Empty cell |
| `1` | Red |
| `2` | Green |
| `3` | Blue |
| `4` | Yellow |
| `5` | Grey |

The black marble is stored separately in the live environment. In serialized snapshots it may use a dedicated code, such as:

```text
9
```

The state encoder converts both representations into the same black-marble feature plane.

Code values are internal implementation details. The neural network receives binary planes rather than raw board codes.

---

## Why Separate Feature Planes Are Used

A single integer-valued board matrix could represent all colours, but separate planes are more suitable for neural-network processing.

Separate planes provide:

- a consistent binary representation,
- no artificial numerical ordering between colours,
- direct compatibility with convolutional layers,
- easier interpretation and debugging,
- a stable representation for ONNX export.

For example, raw codes might incorrectly suggest that grey with code `5` is numerically more significant than red with code `1`. Binary planes avoid this problem.

---

## Feature Vector

Information that is not naturally spatial is stored in an additional feature vector.

The current feature vector has length:

```text
99
```

It contains game-state information such as:

- the current player,
- the current turn,
- forbidden-colour indicators,
- remaining inventory,
- player objective cards,
- shape-related features required by the network.

The resulting neural-network inputs are therefore:

```text
board input:    (batch_size, 6, 7, 7)
feature input:  (batch_size, 99)
```

For a single unbatched state, the corresponding shapes are:

```text
(6, 7, 7)
(99,)
```

---

## Current Player

The current player is represented using the environment convention:

```text
+1  first player
-1  second player
```

The player value is included in the encoded non-spatial features so the network can distinguish otherwise identical board positions in which different players are to move.

This is necessary because the value output is interpreted relative to the active player.

---

## Forbidden-Colour Encoding

The playable colours are represented using a five-element Boolean or binary mask:

```text
[Red, Green, Blue, Yellow, Grey]
```

For example:

```text
[0, 1, 0, 0, 1]
```

means that green and grey are currently forbidden.

The mask allows the network to recognize which placements and replacements are unavailable before legal-action masking is applied.

Although illegal actions are masked during search, including the forbidden colours in the state remains important because they influence the strategic value of the position.

---

## Inventory Encoding

The shared inventory contains one count for each playable colour:

```text
[Red, Green, Blue, Yellow, Grey]
```

The feature vector stores the remaining counts in a fixed order.

Conceptually:

```python
inventory_features = [
    inventory["R"],
    inventory["G"],
    inventory["B"],
    inventory["Y"],
    inventory["Gray"],
]
```

The values may be stored directly or normalized according to the implementation.

Inventory information is required because two visually identical boards may have different legal actions depending on which marbles remain available.

---

## Objective Encoding

Each player has objective cards describing possible winning shapes.

The objective representation is included in the feature vector because the strategic value of a position depends on the active objectives.

The encoding must preserve:

- which shapes belong to the first player,
- which shapes belong to the second player,
- the identity of each shape,
- blocked-colour information associated with a card.

A fixed ordering of all supported shape types is used so every state produces a feature vector of the same length.

The exact ordering must remain unchanged after training begins. Changing it would alter the interpretation of existing checkpoints.

---

## Turn Information

The turn number or related game-progress information may be included in the feature vector.

This helps the network distinguish:

- early-game positions,
- developed positions,
- positions near the configured game-length limit.

Any normalization applied to the turn number must be identical during:

- training,
- Python inference,
- evaluation,
- ONNX inference.

---

## State Encoding Interface

A typical encoding call conceptually looks like:

```python
board_tensor, feature_tensor = encode_state(state)
```

Expected outputs:

| Output | Shape | Description |
|---|---|---|
| `board_tensor` | `(6, 7, 7)` | Spatial marble representation |
| `feature_tensor` | `(99,)` | Non-spatial game information |

Before being passed to the network, a batch dimension is added:

```python
board_tensor = board_tensor.unsqueeze(0)
feature_tensor = feature_tensor.unsqueeze(0)
```

Resulting shapes:

```text
(1, 6, 7, 7)
(1, 99)
```

---

## Batch Encoding

Training operates on mini-batches rather than individual positions.

A batch of size `B` has shapes:

```text
board batch:    (B, 6, 7, 7)
feature batch:  (B, 99)
```

The replay buffer must therefore store enough information to reconstruct both inputs for every training example.

Policy targets have shape:

```text
(B, 2891)
```

Value targets typically have shape:

```text
(B,)
```

or:

```text
(B, 1)
```

depending on the loss implementation.

---

# Action Encoding

## Purpose

The number of legal actions varies between game states, but the neural-network policy head must always produce an output of the same size.

The action encoder solves this by assigning a unique integer index to every action that could theoretically occur on a `7 × 7` board.

The complete policy output has size:

```text
2891
```

Every legal symbolic move maps to one index in the range:

```text
0 <= action_index < 2891
```

---

## Action Categories

The action space is divided into three contiguous regions.

| Action category | Number of actions |
|---|---:|
| Placement | 245 |
| Movement | 2401 |
| Replacement | 245 |
| **Total** | **2891** |

The total is calculated as:

```text
245 + 2401 + 245 = 2891
```

The constants used by the implementation are conceptually:

```python
PLACE_ACTIONS = 245
MOVE_ACTIONS = 2401
REPLACE_ACTIONS = 245
ACTION_SIZE = 2891
```

---

## Board Cell Indexing

Every board coordinate is mapped to a single cell index.

For a board of width `7`, the mapping is:

```text
cell_index = row * 7 + column
```

The cell index range is:

```text
0 to 48
```

Example mappings:

| Coordinate | Cell index |
|---|---:|
| `(0, 0)` | `0` |
| `(0, 6)` | `6` |
| `(1, 0)` | `7` |
| `(3, 3)` | `24` |
| `(6, 6)` | `48` |

The reverse mapping is:

```text
row = cell_index // 7
column = cell_index % 7
```

This mapping must remain identical in both `encode_action` and `decode_action`.

---

## Colour Indexing

Five playable colours are encoded.

| Colour index | Colour |
|---:|---|
| `0` | Red |
| `1` | Green |
| `2` | Blue |
| `3` | Yellow |
| `4` | Grey |

These indices are policy-encoding indices and do not necessarily equal the raw board codes used by the environment.

The black marble is not part of the placement or replacement colour list because it is unique and does not come from the shared inventory.

---

## Placement Action Space

A placement is defined by:

```text
(colour, destination)
```

There are:

```text
5 colours
49 destination cells
```

Therefore:

```text
5 × 49 = 245
```

possible placement actions.

Placement indices occupy:

```text
0 to 244
```

A conceptual encoding formula is:

```text
placement_index = colour_index × 49 + destination_index
```

Example:

```text
colour index:      2
destination index: 10

placement index = 2 × 49 + 10 = 108
```

Whether the move is legal is not determined by this formula. The formula only assigns a stable index.

---

## Movement Action Space

A movement is defined by:

```text
(source, destination)
```

There are:

```text
49 possible source cells
49 possible destination cells
```

Therefore:

```text
49 × 49 = 2401
```

possible movement actions.

Movement indices occupy:

```text
245 to 2645
```

because the movement region begins after the `245` placement entries.

A conceptual encoding formula is:

```text
movement_local_index = source_index × 49 + destination_index

movement_index = 245 + movement_local_index
```

Example:

```text
source index:      24
destination index: 31

local index = 24 × 49 + 31
            = 1207

global index = 245 + 1207
             = 1452
```

The action space includes structurally impossible combinations such as moving from an empty cell or moving to the same cell. These actions remain permanently illegal and are removed by the legal-action mask.

---

## Replacement Action Space

A replacement is represented by:

```text
(replacement colour, target cell)
```

There are:

```text
5 colours
49 target cells
```

Therefore:

```text
5 × 49 = 245
```

possible replacement actions.

Replacement indices occupy:

```text
2646 to 2890
```

The replacement region starts after placement and movement:

```text
replacement_offset = 245 + 2401
                   = 2646
```

A conceptual formula is:

```text
replacement_local_index =
    colour_index × 49 + target_index

replacement_index =
    2646 + replacement_local_index
```

---

## Complete Index Ranges

| Category | Start index | End index | Count |
|---|---:|---:|---:|
| Placement | `0` | `244` | `245` |
| Movement | `245` | `2645` | `2401` |
| Replacement | `2646` | `2890` | `245` |
| **Complete action space** | `0` | `2890` | `2891` |

These boundaries are part of the model interface and must not change without retraining the network.

---

## Symbolic Move Representation

The environment uses tuple-based symbolic moves.

Conceptually, the three move types contain:

```text
placement:
    action type, colour, destination

movement:
    action type, source, destination

replacement:
    action type, colour, target
```

The exact tuple format is defined by the environment and `action_encoding.py`.

The encoder identifies the move category, extracts the required fields, converts coordinates and colours into numeric indices, and applies the appropriate category offset.

---

## Encoding an Action

The public encoding operation is conceptually:

```python
action_index = encode_action(move)
```

The function performs:

1. identify the action type,
2. validate the move structure,
3. convert coordinates to cell indices,
4. convert colour codes to policy colour indices,
5. apply the category-specific formula,
6. return an integer from `0` to `2890`.

The encoder should raise an error for unsupported or malformed move structures rather than silently producing an incorrect index.

---

## Decoding an Action

The reverse operation is conceptually:

```python
move = decode_action(action_index)
```

The decoder first determines the action category from the index range.

```text
0–244:
    placement

245–2645:
    movement

2646–2890:
    replacement
```

It then:

1. subtracts the category offset,
2. extracts colour or source information,
3. extracts the destination or target cell,
4. converts cell indices back to coordinates,
5. returns the symbolic move representation expected by the environment.

Encoding and decoding should satisfy:

```python
decode_action(encode_action(move)) == move
```

for every correctly normalized supported move.

---

## Legal-Action Mask

The network predicts outputs for all `2891` actions, but only a small subset is legal in a particular state.

A legal-action mask is therefore created from:

```python
legal_moves = env.legal_moves()
```

Conceptually:

```python
mask = np.zeros(2891, dtype=bool)

for move in legal_moves:
    action_index = encode_action(move)
    mask[action_index] = True
```

The mask has shape:

```text
(2891,)
```

Entries mean:

```text
True or 1   action is legal
False or 0  action is illegal
```

---

## Masked Policy

The network outputs raw policy logits:

```text
logits shape = (2891,)
```

Before probabilities are computed, illegal actions are excluded.

Conceptually:

```python
masked_logits = logits.copy()
masked_logits[~legal_mask] = -infinity
policy = softmax(masked_logits)
```

The implementation may use a numerically stable custom `masked_softmax`.

After masking:

```text
sum(policy over legal actions) = 1
policy for illegal actions     = 0
```

If the network output contains non-finite values, the implementation may fall back to a uniform distribution over legal actions.

---

## Why Illegal Actions Remain in the Output Space

A smaller dynamic output containing only currently legal moves would be difficult to use because:

- the output dimension would change between positions,
- replay-buffer policy targets would have inconsistent shapes,
- batching would become difficult,
- ONNX export would require dynamic action mapping,
- MCTS statistics would not share a stable index convention.

A fixed action space with legal masking avoids these problems.

---

## Policy Targets

During self-play, Monte Carlo Tree Search produces visit counts for legal root actions.

These counts are converted into a policy target of length `2891`.

Conceptually:

```python
policy_target = np.zeros(2891, dtype=np.float32)

for move, visits in root_visits.items():
    action_index = encode_action(move)
    policy_target[action_index] = visits
```

The vector is then normalized:

```text
policy_target[a] =
    visit_count[a] / total_root_visits
```

Illegal actions remain zero.

The policy head is trained to approximate this MCTS-improved distribution.

---

## Move Selection

During inference or self-play, an action index is selected from the masked policy or from MCTS visit counts.

The selected index is decoded:

```python
selected_index = ...
move = decode_action(selected_index)
```

Before execution, the move should still be checked against the current legal-move set.

This provides additional protection against encoding inconsistencies or stale state data.

---

## Temperature

During early self-play turns, visit counts may be transformed using a temperature parameter.

Conceptually:

```text
π(a) ∝ N(a)^(1 / τ)
```

where:

- `N(a)` is the root visit count,
- `τ` is the temperature.

The resulting probability vector still uses the same `2891`-entry action encoding.

For low temperature, the most visited action is strongly preferred. For higher temperature, move selection becomes more exploratory.

---

## Replay-Buffer Representation

Each training sample stores:

```text
encoded board state
encoded feature vector
policy target of length 2891
value target
```

Conceptually:

```python
training_example = (
    board_tensor,
    feature_vector,
    policy_target,
    value_target,
)
```

Expected dimensions:

| Item | Shape |
|---|---|
| Board tensor | `(6, 7, 7)` |
| Feature vector | `(99,)` |
| Policy target | `(2891,)` |
| Value target | scalar |

All samples therefore have fixed dimensions and can be batched efficiently.

---

## Neural-Network Interface

The network consumes:

```text
board:     (B, 6, 7, 7)
features:  (B, 99)
```

and produces:

```text
policy logits:  (B, 2891)
value:          (B, 1) or (B,)
```

The exact tensor dimensions must agree across:

- `state_encoding.py`,
- `action_encoding.py`,
- `net.py`,
- `mcts.py`,
- `selfplay.py`,
- replay-buffer loading,
- checkpoint loading,
- `export_onnx.py`,
- Unity inference.

---

## ONNX Compatibility

The exported model preserves the same input and output interface.

Typical ONNX inputs are:

```text
board input:
    float tensor with shape (batch, 6, 7, 7)

feature input:
    float tensor with shape (batch, 99)
```

Typical outputs are:

```text
policy logits:
    float tensor with shape (batch, 2891)

value:
    float tensor with shape (batch, 1)
```

The Unity implementation must construct features in the exact same order as the Python encoder.

Matching only the tensor dimensions is insufficient. Every plane and feature position must have the same semantic meaning.

---

## Checkpoint Compatibility

A saved checkpoint assumes fixed definitions for:

- board-plane order,
- feature-vector order,
- feature-vector length,
- colour-index order,
- board-cell mapping,
- action-category offsets,
- policy-output size,
- value perspective.

Changing any of these may make older checkpoints incompatible even if the Python code still loads their tensor dimensions.

Encoding changes should therefore be treated as model-format changes.

---

## Validation Tests

The following encoding tests are particularly important.

### State Encoding Tests

- each marble appears in exactly one board plane,
- empty cells remain zero in every plane,
- the black marble appears in the black plane,
- board tensor shape is `(6, 7, 7)`,
- feature-vector length is `99`,
- forbidden-colour order is stable,
- inventory order is stable,
- player objectives are encoded in a stable order,
- encoding does not mutate the environment.

### Action Encoding Tests

- all legal moves encode to indices in `[0, 2891)`,
- placement indices stay in `[0, 245)`,
- movement indices stay in `[245, 2646)`,
- replacement indices stay in `[2646, 2891)`,
- different canonical moves have different indices,
- encode/decode round trips preserve moves,
- invalid indices raise errors,
- invalid move formats raise errors,
- legal masks contain exactly the generated legal actions.

A useful round-trip test is:

```python
for move in env.legal_moves():
    index = encode_action(move)
    decoded = decode_action(index)

    assert decoded == move
```

Normalization may be required when equivalent move representations use lists in one place and tuples in another.

---

## Common Failure Modes

### Incorrect Feature Order

The network may run without an error while receiving semantically incorrect inputs.

For example, swapping red and green inventory positions does not change the feature shape but changes the meaning of every trained weight.

### Incorrect Player Perspective

If the current player or value target is encoded inconsistently, the network may learn opposite evaluations for otherwise equivalent states.

### Action Offset Errors

An incorrect category offset can cause placement logits to be interpreted as movement or replacement actions.

### Coordinate Convention Mismatch

Using `(x, y)` in one module and `(row, column)` in another can create valid-looking but incorrect moves.

### Stale Legal Masks

A legal mask created before applying a move must not be reused for the successor state.

### Mutable State References

Replay-buffer states must not reference arrays that are later modified by the live environment.

### ONNX Feature Mismatch

The Unity model may produce outputs without runtime errors even when the Unity feature order differs from Python. This makes explicit cross-platform validation essential.

---

## Cross-Platform Validation

Before deploying an ONNX model, the same position should be evaluated in both Python and Unity.

The validation process should compare:

1. board planes,
2. feature vector,
3. policy logits,
4. value output,
5. legal-action indices.

For the same state, the numerical outputs should be equal or very close within floating-point tolerance.

This is the most reliable way to detect encoding differences between the Python and Unity implementations.

---

## Extension Guidelines

### Adding a New State Feature

Adding a feature requires updates to:

- `state_encoding.py`,
- `feat_dim` in the neural network,
- training data generation,
- replay-buffer compatibility,
- checkpoint compatibility,
- ONNX export,
- Unity input construction,
- documentation and tests.

Existing checkpoints cannot normally be reused without adapting the network.

### Adding a New Board Plane

Adding a board plane requires updates to:

- board encoding,
- `board_channels` in the network,
- ONNX input shape,
- Unity input tensor construction,
- saved checkpoint compatibility.

### Adding a New Action Type

Adding a new action category requires:

- assigning a new index range,
- updating `ACTION_SIZE`,
- extending `encode_action`,
- extending `decode_action`,
- modifying legal-mask generation,
- changing the policy-head size,
- updating MCTS statistics,
- retraining the network,
- updating Unity action decoding.

### Changing the Board Size

The current action space assumes a `7 × 7` board with `49` cells.

Changing the board size affects:

- board tensor dimensions,
- cell indexing,
- placement count,
- movement count,
- replacement count,
- action offsets,
- network architecture,
- checkpoints,
- exported models.

The current total of `2891` actions is specific to the `7 × 7` implementation.

---

## Related Documentation

- [Evaluation Function Overview](overview.md)
- [Game Environment](environment.md)
- [Neural Network](neural-network.md)
- [MCTS and Self-Play](mcts-and-self-play.md)
- [Training](training.md)
- [Game Rules](../game-rules.md)
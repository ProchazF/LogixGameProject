# MCTS and Self-Play

[← Back to EvaluationFunction](../../EvaluationFunction/README.md)

## Overview

Monte Carlo Tree Search and self-play form the data-generation part of the training framework.

The neural network does not improve from static examples alone. Instead, it repeatedly plays games against itself, using Monte Carlo Tree Search to choose moves and to create stronger policy targets.

The relevant implementation files are:

```text
logix_az/mcts.py
logix_az/selfplay.py
```

The overall process is:

```text
Current game state
        │
        ▼
Monte Carlo Tree Search
        │
        ▼
Improved move distribution
        │
        ▼
Selected move
        │
        ▼
Next game state
        │
        ▼
Repeat until game end
        │
        ▼
Assign final result to all stored states
```

---

## Role of MCTS

The neural network produces:

- policy logits over all `2891` encoded actions,
- a scalar value estimate.

MCTS uses these predictions to perform a deeper search before choosing a move.

The policy output helps prioritize promising actions.

The value output estimates newly expanded positions without requiring random rollouts to the end of the game.

This combination produces a stronger move distribution than the raw network output alone.

---

## Search Tree

Each MCTS node represents one game state.

The implementation stores action statistics in arrays indexed by encoded actions.

Important node data includes:

| Field | Meaning |
|---|---|
| `P` | Prior probability for each action |
| `N` | Visit count for each action |
| `W` | Accumulated value for each action |
| `children` | Mapping from actions to child nodes |
| `legal_mask` | Mask of legal actions |
| `is_expanded` | Whether the node has been evaluated |
| `value` | Network value associated with the node |

The arrays have length:

```text
2891
```

because they correspond directly to the fixed action space.

---

## Search Simulation

Each MCTS simulation consists of four stages:

1. Selection
2. Expansion
3. Evaluation
4. Backpropagation

A fixed number of simulations is performed before selecting a move.

---

## Selection

Selection starts at the root node and repeatedly chooses an action according to a tree policy.

The implementation balances:

- exploitation of well-performing actions,
- exploration of actions with high prior probability or low visit count.

A typical PUCT-style score is:

```text
Q(s, a) + U(s, a)
```

where:

```text
Q(s, a) = W(s, a) / N(s, a)
```

and:

```text
U(s, a) =
    c_puct × P(s, a) ×
    sqrt(Σb N(s, b)) / (1 + N(s, a))
```

The exploration constant is configured using a parameter such as:

```text
c_puct = 1.5
```

Only legal actions are considered during selection.

---

## Prior Probabilities

When a node is expanded, the network produces policy logits for all actions.

Illegal actions are removed using the node's legal-action mask.

A masked softmax converts the remaining logits into prior probabilities:

```text
P(s, a)
```

The priors satisfy:

```text
P(s, a) = 0 for illegal actions
Σa P(s, a) = 1 over legal actions
```

If the network returns invalid values, the implementation may fall back to a uniform distribution over legal actions.

---

## Expansion

Selection continues until the search reaches a state that has not yet been expanded.

The environment generates:

```python
legal_moves = env.legal_moves()
```

These moves are encoded into the node's legal-action mask.

The network then evaluates the position.

The node stores:

- masked policy priors,
- legal actions,
- predicted value,
- expanded status.

Child nodes may be created immediately or lazily when an action is selected later.

---

## Neural-Network Evaluation

The current state is encoded using:

```text
board tensor:   (6, 7, 7)
feature vector: (99,)
```

The network returns:

```text
policy logits: (2891,)
value:         scalar
```

The policy is used to initialize action priors.

The value is used instead of performing a random simulation until the end of the game.

---

## Terminal Nodes

If a simulation reaches a terminal state, the environment result is used directly.

The terminal result must be converted to the perspective expected by MCTS.

Typical global results are:

```text
+1  first player wins
 0  draw
-1  second player wins
```

The value passed into backpropagation must remain consistent with the active-player convention.

Incorrect perspective handling can cause the search to prefer losing moves.

---

## Backpropagation

After expansion or terminal evaluation, the value is propagated back through the selected path.

For every traversed state-action pair:

- visit count `N` is increased,
- accumulated value `W` is updated,
- the value sign changes when moving between player perspectives.

Conceptually:

```text
N(s, a) ← N(s, a) + 1
W(s, a) ← W(s, a) + v
v       ← -v
```

The sign change is necessary because consecutive nodes belong to opposing players.

The resulting mean action value is:

```text
Q(s, a) = W(s, a) / N(s, a)
```

---

## Root Visit Counts

After all simulations have completed, the root node contains visit counts for legal actions.

These counts represent the search-improved move preferences.

Conceptually:

```text
N(root, a)
```

The visit counts are used for two purposes:

1. selecting the move played in self-play,
2. creating the policy target stored for training.

---

## Policy Target

The MCTS policy target has length:

```text
2891
```

For each legal action:

```text
π(a) =
    N(root, a) / Σb N(root, b)
```

Illegal actions remain zero.

This target is stored together with the current state.

The network is later trained to reproduce this improved distribution.

---

## Temperature

Temperature controls how visit counts are converted into move probabilities.

A common transformation is:

```text
π(a) ∝ N(root, a)^(1 / τ)
```

where:

- `τ` is the temperature,
- larger values increase exploration,
- smaller values favor the most visited move.

During early self-play turns, a non-zero temperature encourages varied games.

After a configured number of turns, the implementation may choose the most visited action deterministically.

---

## Move Selection

A move is selected from the MCTS policy.

During exploratory self-play:

```python
action_index = sample(policy)
```

During deterministic play:

```python
action_index = argmax(root_visit_counts)
```

The selected action index is decoded back into the symbolic move format expected by the environment.

Before execution, the move should correspond to one of:

```python
env.legal_moves()
```

---

## Self-Play Game

A self-play game repeatedly performs MCTS from the current state.

A simplified loop is:

```python
while not done:
    state = snapshot(env)

    policy = mcts.search(env)

    move = select_move(policy)

    stored_positions.append(
        (state, policy, env.player)
    )

    _, done, result = env.step(move)
```

After the game ends, the final result is converted into a value target for every stored position.

---

## Stored Self-Play Data

Before the game ends, each stored sample contains:

```text
state
MCTS policy
player at state
```

After termination, the final result is added:

```text
state
MCTS policy
value target
```

The final training sample contains:

```text
board tensor:   (6, 7, 7)
feature vector: (99,)
policy target:  (2891,)
value target:   scalar
```

---

## Value-Target Assignment

Suppose the final result is represented globally as:

```text
+1  first player wins
-1  second player wins
```

For a stored state, the value target is conceptually:

```text
value_target =
    final_result × player_at_state
```

This produces:

```text
+1  the player to move eventually wins
 0  the game is drawn
-1  the player to move eventually loses
```

This convention must match the value-head interpretation and MCTS backup logic.

---

## Draws

A self-play game may end in a draw when:

- no winner is found before the maximum game length,
- the environment explicitly returns a draw.

Drawn positions receive:

```text
value_target = 0
```

Draw games still provide valid policy targets and can therefore contribute useful training data.

---

## Self-Play Function

The main self-play entry point is conceptually:

```python
play_one_game(
    env,
    mcts,
    num_sims=200,
    tau_moves=10,
)
```

Important parameters include:

| Parameter | Meaning |
|---|---|
| `env` | Logix environment |
| `mcts` | Search instance using the current network |
| `num_sims` | Number of MCTS simulations per move |
| `tau_moves` | Number of early turns using exploratory temperature |

The exact defaults are defined in the implementation.

---

## Number of Simulations

The number of simulations affects both playing strength and execution time.

More simulations usually provide:

- stronger move selection,
- more reliable policy targets,
- more expensive self-play.

Fewer simulations provide:

- faster game generation,
- weaker and noisier targets.

A typical configuration may use:

```text
200 simulations per move
```

but the value can be changed depending on hardware and training goals.

---

## Tree Reuse

After a move is selected, the corresponding child node may be reused as the root of the next search.

Tree reuse can preserve useful search statistics and reduce repeated work.

If the current implementation rebuilds the tree after every move, the search remains correct but may perform more neural evaluations.

Any reused tree must correspond exactly to the successor environment state.

---

## Root Noise

AlphaZero-style self-play commonly adds noise to root priors to encourage exploration.

A conceptual modification is:

```text
P'(a) =
    (1 - ε) P(a) + ε η(a)
```

where `η` is sampled from a Dirichlet distribution.

Whether root noise is used depends on the current implementation and training configuration.

If enabled, it should be applied only at the root during self-play, not during deterministic evaluation.

---

## Immediate Tactical Checks

Some agents or search configurations may perform immediate win detection before running the full search.

This can:

- avoid missing one-move wins,
- save MCTS simulations,
- improve tactical reliability.

Such checks must use the same legal-move and win-detection logic as the environment.

---

## Environment Simulation

MCTS repeatedly creates successor states.

A typical operation is:

```python
child_env = env.simulate_move(move)
```

The simulated environment must be independent of the parent.

Modifying a child must not change:

- the root environment,
- sibling states,
- previously stored snapshots.

Incorrect copying can corrupt the search tree.

---

## Search Caching

Neural-network evaluation is expensive.

Possible optimizations include caching:

- encoded states,
- policy and value outputs,
- legal-action masks,
- successor states.

A cache key must be immutable and uniquely represent the complete game state, including:

- board,
- player,
- inventory,
- forbidden colours,
- objectives,
- turn-related information.

Using mutable lists directly as dictionary keys causes errors such as:

```text
TypeError: unhashable type: 'list'
```

State keys should therefore use tuples, bytes, or another immutable representation.

---

## Numerical Stability

Masked policy computation must handle invalid network output safely.

Potential problems include:

- NaN logits,
- infinite logits,
- no legal actions,
- zero visit counts,
- division by zero.

A robust implementation should:

- verify that at least one legal action exists,
- ignore illegal logits,
- use stable softmax computation,
- fall back to a uniform legal policy when necessary,
- report repeated numerical failures.

---

## MCTS Parameters

Common configurable parameters include:

| Parameter | Purpose |
|---|---|
| `num_sims` | Simulations performed per move |
| `c_puct` | Exploration strength |
| `temperature` | Move-selection randomness |
| `tau_moves` | Number of exploratory opening turns |
| root noise parameters | Additional self-play exploration |
| maximum game length | Draw limit |

Changing these parameters affects:

- self-play diversity,
- search strength,
- training speed,
- policy-target quality.

---

## Self-Play Diversity

Self-play must balance strength and variation.

Too little exploration may produce:

- repetitive openings,
- narrow training data,
- overfitting to a limited set of positions.

Too much exploration may produce:

- weak games,
- noisy policy targets,
- slower improvement.

Temperature, root noise, random seeds, and MCTS simulation count all influence this balance.

---

## Performance Considerations

Self-play is typically the most expensive stage of training.

Each move may involve hundreds of simulations, and every simulation can require:

- legal-move generation,
- state copying,
- state encoding,
- network inference,
- tree traversal,
- value backpropagation.

Possible optimizations include:

- batched network inference,
- tree reuse,
- evaluation caching,
- faster environment copies,
- parallel self-play workers,
- reduced Python object allocation,
- GPU inference.

Correctness should be verified before introducing aggressive optimization.

---

## Deterministic Evaluation

When comparing trained models, self-play exploration should usually be disabled.

A deterministic evaluation configuration commonly uses:

- no root noise,
- very low or zero temperature,
- fixed random seeds where applicable,
- equal simulation budgets,
- alternating player positions.

This ensures that differences in results are primarily caused by agent strength rather than exploration randomness.

---

## Common Failure Modes

### Incorrect Value Sign

If the value sign is not inverted between player turns, MCTS may optimize for the opponent.

### Stale Legal Mask

A legal mask from one state must not be reused after the environment changes.

### Mutated Parent State

Successor simulation must not modify the original environment.

### Invalid Action Decoding

An encoded action must decode to the exact move representation expected by `env.step`.

### Empty Legal-Move Set

The search must handle terminal or no-move states explicitly.

### Zero Visit Counts

Policy-target normalization must avoid division by zero.

### Excessive Self-Play Determinism

Always choosing the same root action can reduce training-data diversity.

### Incompatible Network Dimensions

MCTS expects:

```text
policy size = 2891
value size  = scalar
```

A mismatched model cannot be used safely.

---

## Testing MCTS

Important MCTS tests include:

- priors sum to one over legal actions,
- illegal actions have zero prior,
- visit counts increase after simulations,
- terminal values are backed up correctly,
- value signs alternate by depth,
- selected actions are legal,
- parent environments remain unchanged,
- immediate wins are preferred,
- deterministic settings produce repeatable choices,
- invalid logits trigger a safe fallback.

---

## Testing Self-Play

Important self-play tests include:

- every stored policy has length `2891`,
- every stored board tensor has shape `(6, 7, 7)`,
- every feature vector has length `99`,
- policies contain no probability on illegal actions,
- policy probabilities sum to one,
- value targets match the stored player perspective,
- drawn games assign zero values,
- games terminate at the configured maximum length,
- generated samples can be loaded by the replay buffer.

---

## Relationship to Training

MCTS and self-play generate the supervision used by the neural network.

The feedback loop is:

```text
Neural network
      │
      ▼
Guided MCTS
      │
      ▼
Improved policies
      │
      ▼
Training examples
      │
      ▼
Updated neural network
```

The network improves the search, and the search produces stronger targets for the network.

This mutual improvement is the central mechanism of the training framework.

---

## Files Involved

| File | Responsibility |
|---|---|
| `logix_az/mcts.py` | Search tree, selection, expansion, evaluation, and backup |
| `logix_az/selfplay.py` | Complete self-play game generation |
| `logix_az/state_encoding.py` | Neural-network input creation |
| `logix_az/action_encoding.py` | Action indexing and decoding |
| `logix_az/net.py` | Policy and value predictions |
| `logix_az/env_logix_helper.py` | Legal moves and successor-state simulation |
| `logix_az/replay_buffer.py` | Storage of generated training samples |
| `train.py` | Coordinates repeated self-play and optimization |

---

## Related Documentation

- [Evaluation Function Overview](overview.md)
- [Game Environment](environment.md)
- [State and Action Encoding](state-and-action-encoding.md)
- [Neural Network](neural-network.md)
- [Training](training.md)
- [Bot Experiments](../bot-experiments/overview.md)
import numpy as np


def visits_to_pi(visits, tau: float, legal_mask):
    """
    Convert MCTS visit counts into a probability distribution.
    Falls back to uniform over legal moves if visits are degenerate.
    """
    legal_mask = legal_mask.astype(bool)

    v = visits.copy().astype(np.float32)
    v[~legal_mask] = 0.0

    num_legal = int(legal_mask.sum())
    if num_legal == 0:
        raise ValueError("No legal moves available in a non-terminal state.")

    if tau <= 1e-6:
        pi = np.zeros_like(v, dtype=np.float32)
        best = np.argmax(v)
        pi[best] = 1.0
        return pi

    v = v ** (1.0 / tau)
    s = v.sum()

    if not np.isfinite(s) or s <= 0:
        # fallback: uniform over legal moves
        pi = np.zeros_like(v, dtype=np.float32)
        pi[legal_mask] = 1.0 / num_legal
        return pi

    pi = v / s

    if not np.all(np.isfinite(pi)):
        pi = np.zeros_like(v, dtype=np.float32)
        pi[legal_mask] = 1.0 / num_legal
        return pi

    return pi


def play_one_game(env, mcts, num_sims=200, tau_moves=10):
    """
    Play one self-play game and return training examples:
      [(state, pi, z), ...]

    where:
      - state is the position before a move
      - pi is the improved policy from MCTS visit counts
      - z is the final outcome from the perspective of the player to move in that state
    """
    data = []   # list of (state, pi, player_to_move)
    state = env.reset()

    move_idx = 0

    while not env.is_terminal(state):
        legal = env.legal_actions_mask(state)
        visits = mcts.run(state, num_sims=num_sims)

        tau = 1.0 if move_idx < tau_moves else 0.1
        pi = visits_to_pi(visits, tau, legal)

        # store the player to move for later sign correction
        data.append((state, pi, state.player))

        action = np.random.choice(len(pi), p=pi)
        state = env.step(state, action)
        move_idx += 1

    # terminal outcome is from the perspective of the player to move in the terminal state
    z_terminal = env.outcome(state)
    terminal_player = state.player

    examples = []
    for s, pi, player in data:
        # If stored state's player matches terminal state's player, use same sign.
        # Otherwise flip sign.
        z = z_terminal if player == terminal_player else -z_terminal
        examples.append((s, pi, z))

    return examples
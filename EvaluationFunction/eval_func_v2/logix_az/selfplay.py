import numpy as np


def visits_to_pi(visits, tau: float, legal_mask):
    """
    Convert MCTS visit counts into a probability distribution.
    """
    v = visits.copy()
    v[~legal_mask] = 0.0

    if tau <= 1e-6:
        pi = np.zeros_like(v, dtype=np.float32)
        best = np.argmax(v)
        pi[best] = 1.0
        return pi

    v = v.astype(np.float32) ** (1.0 / tau)
    s = v.sum()
    return v / (s + 1e-8)


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
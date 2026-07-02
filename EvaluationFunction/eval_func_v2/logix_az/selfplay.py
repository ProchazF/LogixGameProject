import numpy as np

def find_immediate_winning_action(env, state, legal_mask):
    current_player = state.player

    for action in np.where(legal_mask)[0]:
        next_state = env.step(state, int(action))

        if env.is_terminal(next_state):
            # Terminal winner check through absolute player identity
            if env.outcome(next_state) > 0 and next_state.player == current_player:
                return int(action)

    return None

import numpy as np


def find_safe_action(env, state, pi, legal_mask, top_k=20):
    legal_actions = np.where(legal_mask)[0]

    # first: immediate win
    for action in legal_actions:
        next_state = env.step(state, int(action))
        if env.is_terminal(next_state) and env.outcome(next_state) > 0:
            return int(action)

    # only check top-k moves according to MCTS policy
    ranked = legal_actions[np.argsort(pi[legal_actions])[::-1]]
    candidates = ranked[:top_k]

    safe_actions = []

    for action in candidates:
        next_state = env.step(state, int(action))

        if env.is_terminal(next_state):
            continue

        opp_legal = env.legal_actions_mask(next_state)
        opponent_can_win = False

        for opp_action in np.where(opp_legal)[0]:
            after_opp = env.step(next_state, int(opp_action))
            if env.is_terminal(after_opp) and env.outcome(after_opp) > 0:
                opponent_can_win = True
                break

        if not opponent_can_win:
            safe_actions.append(int(action))

    if safe_actions:
        safe_pi = np.zeros_like(pi, dtype=np.float32)
        safe_pi[safe_actions] = pi[safe_actions]

        if safe_pi.sum() > 0:
            safe_pi /= safe_pi.sum()
            return int(np.random.choice(len(safe_pi), p=safe_pi))

        return int(np.random.choice(safe_actions))

    # fallback: use MCTS normally
    return int(np.random.choice(len(pi), p=pi))

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


def play_one_game(env, mcts, num_sims=200, tau_moves=20):
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

        tau = 1.5 if move_idx < tau_moves else 0.5
        pi = visits_to_pi(visits, tau, legal)

        # store the player to move for later sign correction
        data.append((state, pi, state.player))

        # winning_action = find_immediate_winning_action(env, state, legal)

        # if winning_action is not None:
        #     action = winning_action
        # else:
        #     # action = np.random.choice(len(pi), p=pi)
        #     action = find_safe_action(env, state, pi, legal, top_k=10)

        action = find_safe_action(env, state, pi, legal, top_k=10)

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

    if z_terminal == 0.0:
        examples = examples[::3]

    return examples
# selfplay.py
import numpy as np

def visits_to_pi(visits, tau: float, legal_mask):
    v = visits.copy()
    v[~legal_mask] = 0
    if tau <= 1e-6:
        pi = np.zeros_like(v)
        pi[np.argmax(v)] = 1.0
        return pi
    v = v ** (1.0 / tau)
    s = v.sum()
    return v / (s + 1e-8)

def play_one_game(env, mcts, num_sims=200, tau_moves=10):
    data = []  # list of (state, pi)
    state = env.reset()

    move_idx = 0
    while not env.is_terminal(state):
        legal = env.legal_actions_mask(state)
        visits = mcts.run(state, num_sims=num_sims)
        tau = 1.0 if move_idx < tau_moves else 0.1
        pi = visits_to_pi(visits, tau, legal)

        data.append((state, pi))
        action = np.random.choice(len(pi), p=pi)
        state = env.step(state, action)
        move_idx += 1

    z = env.outcome(state)  # for player-to-move at terminal
    # If you canonicalize every stored state to player-to-move perspective, you can attach z directly.
    # Otherwise you'll need to flip z on alternating turns. Keep it simple: canonicalize.
    examples = [(s, pi, z) for (s, pi) in data]
    return examples
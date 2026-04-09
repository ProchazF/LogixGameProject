# mcts.py
import numpy as np
import torch

from .state_encoding import encode_state

class Node:
    __slots__ = ("P","N","W","children","is_expanded","legal_mask","value")
    def __init__(self, A):
        self.P = np.zeros(A, dtype=np.float32)   # prior probabilities
        self.N = np.zeros(A, dtype=np.int32)     # visit counts
        self.W = np.zeros(A, dtype=np.float32)   # total value
        self.children = {}
        self.is_expanded = False
        self.legal_mask = None
        self.value = 0.0

def masked_softmax(logits: np.ndarray, mask: np.ndarray):
    mask = mask.astype(bool)

    if mask.sum() == 0:
        raise ValueError("masked_softmax received no legal actions.")

    x = np.array(logits, dtype=np.float32, copy=True)

    if not np.all(np.isfinite(x)):
        # fallback to uniform over legal actions
        p = np.zeros_like(x, dtype=np.float32)
        p[mask] = 1.0 / mask.sum()
        return p

    x[~mask] = -1e9
    x = x - np.max(x)

    e = np.exp(x)
    e[~mask] = 0.0
    s = e.sum()

    if not np.isfinite(s) or s <= 0:
        p = np.zeros_like(x, dtype=np.float32)
        p[mask] = 1.0 / mask.sum()
        return p

    return e / s

class MCTS:
    def __init__(self, env, net, A, c_puct=1.5, device="cpu"):
        self.env = env
        self.net = net
        self.A = A
        self.c_puct = c_puct
        self.device = device
        self.nodes = {}  # hash(state) -> Node

    def _hash(self, state):
        """
        Build a stable hash from the actual current LogixState fields.
        """
        obj_repr = repr(state.objectives).encode("utf-8")

        return hash((
            state.board.tobytes(),
            int(state.player),
            int(state.turn),
            state.banned.tobytes(),
            state.inventory.tobytes(),
            obj_repr,
        ))

    @torch.no_grad()
    def _eval(self, state):
        bp, feat = encode_state(state)
        bp = bp.unsqueeze(0).to(self.device)
        feat = feat.unsqueeze(0).to(self.device)
        logits, v = self.net(bp, feat)
        return logits.squeeze(0).cpu().numpy(), float(v.item())

    def run(self, root_state, num_sims: int):
        root_state = self.env.canonicalize(root_state)
        root = self._get_node(root_state)

        for _ in range(num_sims):
            self._simulate(root_state)

        visits = root.N.astype(np.float32)
        if root.legal_mask is not None:
            visits[~root.legal_mask] = 0.0
        return visits

    def _get_node(self, state):
        h = self._hash(state)
        if h not in self.nodes:
            self.nodes[h] = Node(self.A)
        return self.nodes[h]

    def _simulate(self, state):
        state = self.env.canonicalize(state)
        node = self._get_node(state)

        # terminal node
        if self.env.is_terminal(state):
            return self.env.outcome(state)

        # expansion
        if not node.is_expanded:
            legal = self.env.legal_actions_mask(state)
            logits, v = self._eval(state)
            P = masked_softmax(logits, legal)

            node.P = P
            node.legal_mask = legal
            node.is_expanded = True
            node.value = v
            return v

        # selection
        Nsum = node.N.sum()
        best_a = -1
        best_score = -1e9

        for a in np.where(node.legal_mask)[0]:
            # PUCT formula
            Q = (node.W[a] / node.N[a]) if node.N[a] > 0 else 0.0 # how good the move is on average - Q
            U = self.c_puct * node.P[a] * np.sqrt(Nsum + 1e-8) / (1 + node.N[a]) # exploration bonus - if low visits and good eval by net or when we search a lot elsewhere
            score = Q + U

            if score > best_score:
                best_score = score
                best_a = a

        if best_a == -1:
            # should not happen if legal mask is correct
            return 0.0

        # transition
        next_state = self.env.step(state, best_a)

        # recursive evaluation from opponent perspective
        v = -self._simulate(next_state)

        # backup
        node.N[best_a] += 1
        node.W[best_a] += v
        return v
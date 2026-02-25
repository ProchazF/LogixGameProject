# replay_buffer.py
import random
from collections import deque

class ReplayBuffer:
    def __init__(self, max_size=200_000):
        self.buf = deque(maxlen=max_size)

    def add_game(self, examples):
        self.buf.extend(examples)

    def sample(self, batch_size):
        return random.sample(self.buf, batch_size)

    def __len__(self):
        return len(self.buf)
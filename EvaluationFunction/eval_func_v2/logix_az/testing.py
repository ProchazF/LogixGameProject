from env_logix_helper import LogixShapeEnv
from action_encoding import encode_action, decode_action

env = LogixShapeEnv()
env.reset()

moves = env.legal_moves()

for mv in moves:
    a = encode_action(mv)
    mv2 = decode_action(a)
    if mv != mv2:
        print("Mismatch:", mv, a, mv2)

print("Done")
# action_encoding.py
import numpy as np

N = 7
COLORS = 5  # R,G,B,Y,Gray
DIRS = 4
MAX_DIST = 6

PLACE_OFFSET = 0
PLACE_SIZE   = N*N*COLORS

MOVE_OFFSET  = PLACE_OFFSET + PLACE_SIZE
MOVE_SIZE    = N*N*DIRS*MAX_DIST

SWAP_OFFSET  = MOVE_OFFSET + MOVE_SIZE
SWAP_SIZE    = N*N*COLORS

A = PLACE_SIZE + MOVE_SIZE + SWAP_SIZE

def decode_action(a: int):
    # returns a structured move like ("place", x, y, c) etc.
    if a < PLACE_SIZE:
        t = a
        cell = t // COLORS
        c = t % COLORS
        x = cell % N
        y = cell // N
        return ("place", x, y, c)

    a -= PLACE_SIZE
    if a < MOVE_SIZE:
        t = a
        cell = t // (DIRS*MAX_DIST)
        rem  = t %  (DIRS*MAX_DIST)
        d = rem // MAX_DIST
        dist = (rem % MAX_DIST) + 1
        x = cell % N
        y = cell // N
        return ("move", x, y, d, dist)

    a -= MOVE_SIZE
    if a < SWAP_SIZE:
        t = a
        cell = t // COLORS
        c = t % COLORS
        x = cell % N
        y = cell // N
        return ("swap", x, y, c)

    raise ValueError("action out of range")

def encode_action(move) -> int:
    # inverse of decode_action
    raise NotImplementedError
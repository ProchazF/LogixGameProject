import sys
import pygame
import torch
import numpy as np

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from logix_az.env_logix_helper import LogixShapeEnv
from logix_az.env_logix import LogixEnv
from logix_az.net import LogixNet
from logix_az.mcts import MCTS
from logix_az.action_encoding import A, decode_action

CHECKPOINT = "checkpoints/net_011300.pt"

CELL = 75
N = 7
SIDE = CELL * N
PANEL_W = 520
W, H = SIDE + PANEL_W, 900

COLORS = {
    "bg": (235,235,235),
    "grid": (40,40,40),
    "button": (220,220,220),
    "select": (255,150,0),
    "text": (20,20,20),
    "R": (220,50,50),
    "G": (60,170,80),
    "B": (60,100,220),
    "Y": (230,210,60),
    "Gray": (150,150,150),
    "Black": (20,20,20),
}

CODE_TO_COLOR = {1:"R", 2:"G", 3:"B", 4:"Y", 5:"Gray"}
buttons = []


def text(screen, s, x, y, size=22):
    font = pygame.font.SysFont(None, size)
    screen.blit(font.render(str(s), True, COLORS["text"]), (x, y))


def draw_button(screen, rect, label, selected=False):
    pygame.draw.rect(screen, COLORS["select"] if selected else COLORS["button"], rect)
    pygame.draw.rect(screen, COLORS["grid"], rect, 2)
    text(screen, label, rect.x + 8, rect.y + 8, 22)


def draw_board(screen, env, selected_cell=None):
    for r in range(N):
        for c in range(N):
            rect = pygame.Rect(c * CELL, r * CELL, CELL, CELL)
            pygame.draw.rect(screen, (245,245,245), rect)
            pygame.draw.rect(screen, COLORS["grid"], rect, 2)

            if selected_cell == (r, c):
                pygame.draw.rect(screen, COLORS["select"], rect, 5)

            cx, cy = c * CELL + CELL // 2, r * CELL + CELL // 2

            if env.black[r, c] == 1:
                pygame.draw.circle(screen, COLORS["Black"], (cx, cy), 25)
            else:
                v = int(env.board[r, c])
                if v:
                    pygame.draw.circle(screen, COLORS[CODE_TO_COLOR[v]], (cx, cy), 25)


def normalize_shape_offsets(offsets):
    min_r = min(r for r, c in offsets)
    min_c = min(c for r, c in offsets)
    return [(r - min_r, c - min_c) for r, c in offsets]


def draw_shape_preview(screen, obj, x, y, scale=24):
    shape = obj["shape"]
    assigned = obj["assigned_color"]
    offsets = normalize_shape_offsets(shape.offsets)

    text(screen, shape.name, x, y, 19)
    text(screen, f"forbidden: {assigned}", x, y + 20, 17)

    for dr, dc in offsets:
        rect = pygame.Rect(
            x + dc * scale,
            y + 45 + dr * scale,
            scale - 2,
            scale - 2,
        )
        pygame.draw.rect(screen, COLORS[assigned], rect)
        pygame.draw.rect(screen, COLORS["grid"], rect, 1)


def draw_panel(screen, env, selected_color, mode, status):
    global buttons
    buttons = []

    x = SIDE + 20
    y = 20

    text(screen, "Human: Player +1", x, y); y += 28
    text(screen, "Bot: Player -1", x, y); y += 28
    text(screen, f"Turn/player: {env.player}", x, y); y += 28
    text(screen, f"Banned: {sorted(env.banned_colors())}", x, y); y += 34
    text(screen, status, x, y, 20); y += 36

    text(screen, "Mode:", x, y)
    bx = x
    for label, m in [("Place", "place"), ("Move", "move"), ("Replace", "replace")]:
        rect = pygame.Rect(bx, y + 28, 110, 36)
        draw_button(screen, rect, label, selected=(mode == m))
        buttons.append((rect, ("mode", m)))
        bx += 120
    y += 78

    text(screen, "Color:", x, y)
    bx = x
    for col in ("R", "G", "B", "Y", "Gray"):
        rect = pygame.Rect(bx, y + 28, 90, 36)
        draw_button(screen, rect, col, selected=(selected_color == col))
        pygame.draw.circle(screen, COLORS[col], (rect.right - 17, rect.centery), 9)
        buttons.append((rect, ("color", col)))
        bx += 98
    y += 78

    text(screen, "Inventory:", x, y); y += 28
    for col in ("R", "G", "B", "Y", "Gray"):
        pygame.draw.circle(screen, COLORS[col], (x + 12, y + 10), 10)
        text(screen, f"{col}: {env.inventory[col]}", x + 30, y, 20)
        y += 24

    y += 20
    text(screen, "Cards:", x, y, 24); y += 34

    for who in (+1, -1):
        text(screen, f"Player {who}", x, y, 22)
        y += 25

        ox = x
        for obj in env.objectives[who]:
            draw_shape_preview(screen, obj, ox, y, scale=24)
            ox += 230

        y += 150

    text(screen, "Move: click source then target.", x, H - 58, 18)
    text(screen, "ESC = quit", x, H - 36, 18)


def load_bot(device):
    ckpt = torch.load(CHECKPOINT, map_location=device)

    board_channels = ckpt.get("board_channels", 6)
    feat_dim = ckpt.get("feat_dim", 99)

    net = LogixNet(board_channels, feat_dim).to(device)
    net.load_state_dict(ckpt["state_dict"])
    net.eval()

    return net


def bot_choose_move(helper_env, net, device, num_sims=100):
    wrapper = LogixEnv(n=helper_env.n, max_game_len=helper_env.max_game_len)
    state = wrapper._pack_state(helper_env)

    mcts = MCTS(wrapper, net, A, c_puct=1.5, device=device)
    visits = mcts.run(state, num_sims=num_sims)

    legal = wrapper.legal_actions_mask(state)
    visits[~legal] = 0

    if visits.sum() <= 0:
        legal_actions = np.where(legal)[0]
        action = int(np.random.choice(legal_actions))
    else:
        action = int(np.argmax(visits))

    return decode_action(action)


def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Logix: Human vs Bot")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("loading bot on", device)
    net = load_bot(device)

    env = LogixShapeEnv(n=7, max_game_len=100, seed=None)

    selected_color = "R"
    mode = "place"
    selected_cell = None
    status = "Your move."

    while True:
        screen.fill(COLORS["bg"])
        draw_board(screen, env, selected_cell)
        draw_panel(screen, env, selected_color, mode, status)
        pygame.display.flip()

        if env.player == -1:
            status = "Bot thinking..."
            screen.fill(COLORS["bg"])
            draw_board(screen, env, selected_cell)
            draw_panel(screen, env, selected_color, mode, status)
            pygame.display.flip()

            bot_move = bot_choose_move(env, net, device, num_sims=100)

            if bot_move not in env.legal_moves():
                print("Bot chose illegal move:", bot_move)
                legal = env.legal_moves()
                bot_move = legal[0]

            _, done, result = env.step(bot_move)
            print("Bot played:", bot_move)
            status = f"Bot played {bot_move}"

            if done:
                status = f"Game over. Result: {result}"
                print(status)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and env.player == +1:
                mx, my = pygame.mouse.get_pos()

                clicked_button = False
                for rect, action in buttons:
                    if rect.collidepoint(mx, my):
                        kind, value = action
                        if kind == "mode":
                            mode = value
                            selected_cell = None
                        elif kind == "color":
                            selected_color = value
                        clicked_button = True
                        break

                if clicked_button:
                    continue

                if mx >= SIDE or my >= SIDE:
                    continue

                r, c = my // CELL, mx // CELL

                if mode == "place":
                    move = ("place", r, c, selected_color)

                elif mode == "replace":
                    move = ("replace", r, c, selected_color)

                elif mode == "move":
                    if selected_cell is None:
                        selected_cell = (r, c)
                        continue
                    r1, c1 = selected_cell
                    move = ("move", r1, c1, r, c)
                    selected_cell = None

                if move not in env.legal_moves():
                    status = f"Invalid move: {move}"
                    print(status)
                    continue

                _, done, result = env.step(move)
                status = f"You played {move}"

                if done:
                    status = f"Game over. Result: {result}"
                    print(status)


if __name__ == "__main__":
    main()
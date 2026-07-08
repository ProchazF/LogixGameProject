import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LOGIX_ROOT = REPO_ROOT / "EvaluationFunction" / "eval_func_v2"
sys.path.insert(0, str(LOGIX_ROOT))

import pygame

from bots import (
    RandomBot,
    HeuristicBot,
    NeuralAlphaBetaBot,
    MCTSBot,
)

from logix_az.env_logix_helper import LogixShapeEnv


# ============================================================
# CONFIG
# ============================================================

BOT_TO_PLAY_AGAINST = "MCTS-new-100"
# Options:
# "Random"
# "Heuristic"
# "AlphaBeta-new-d3"
# "MCTS-old-100"
# "MCTS-new-100"

HUMAN_PLAYER = +1
BOT_PLAYER = -1

MAX_GAME_LEN = 100

OLD_CKPT = "EvalFunction/net_010000.pt"
NEW_CKPT = "EvalFunction/net_015200.pt"


# ============================================================
# GUI CONSTANTS
# ============================================================

CELL = 75
N = 7
SIDE = CELL * N
PANEL_W = 620
W, H = SIDE + PANEL_W, max(SIDE, 920)

COLORS = {
    "bg": (235, 235, 235),
    "grid": (40, 40, 40),
    "button": (220, 220, 220),
    "select": (255, 150, 0),
    "text": (20, 20, 20),

    "R": (220, 50, 50),
    "G": (60, 170, 80),
    "B": (60, 100, 220),
    "Y": (230, 210, 60),
    "Gray": (150, 150, 150),
    "Black": (20, 20, 20),
}

CODE_TO_COLOR = {
    1: "R",
    2: "G",
    3: "B",
    4: "Y",
    5: "Gray",
}

buttons = []


# ============================================================
# DRAWING
# ============================================================

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

            pygame.draw.rect(screen, (245, 245, 245), rect)
            pygame.draw.rect(screen, COLORS["grid"], rect, 2)

            if selected_cell == (r, c):
                pygame.draw.rect(screen, COLORS["select"], rect, 5)

            cx = c * CELL + CELL // 2
            cy = r * CELL + CELL // 2

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
    text(screen, f"not {assigned}", x, y + 20, 17)

    for dr, dc in offsets:
        rect = pygame.Rect(
            x + dc * scale,
            y + 45 + dr * scale,
            scale - 2,
            scale - 2,
        )

        pygame.draw.rect(screen, COLORS[assigned], rect)
        pygame.draw.rect(screen, COLORS["grid"], rect, 1)

        if (dr, dc) == offsets[0]:
            pygame.draw.circle(screen, COLORS["Black"], rect.center, 4)


def draw_panel(screen, env, selected_color, mode, status, bot_name):
    global buttons
    buttons = []

    x = SIDE + 20
    y = 20

    text(screen, "Human: Player +1", x, y)
    y += 28

    text(screen, f"Bot: Player -1 ({bot_name})", x, y)
    y += 28

    text(screen, f"Turn/player: {env.player}", x, y)
    y += 28

    text(screen, f"Game turn: {env.turn}", x, y)
    y += 28

    text(screen, f"Banned: {sorted(env.banned_colors())}", x, y)
    y += 34

    text(screen, status, x, y, 20)
    y += 40

    text(screen, "Mode:", x, y)
    bx = x

    for label, m in [
        ("Place", "place"),
        ("Move", "move"),
        ("Replace", "replace"),
    ]:
        rect = pygame.Rect(bx, y + 28, 110, 36)
        draw_button(screen, rect, label, selected=(mode == m))
        buttons.append((rect, ("mode", m)))
        bx += 120

    y += 78

    text(screen, "Color:", x, y)
    bx = x

    for col in ("R", "G", "B", "Y", "Gray"):
        rect = pygame.Rect(bx, y + 28, 95, 36)
        draw_button(screen, rect, col, selected=(selected_color == col))
        pygame.draw.circle(screen, COLORS[col], (rect.right - 18, rect.centery), 10)
        buttons.append((rect, ("color", col)))
        bx += 105

    y += 82

    text(screen, "Inventory:", x, y)
    y += 28

    for col in ("R", "G", "B", "Y", "Gray"):
        pygame.draw.circle(screen, COLORS[col], (x + 12, y + 10), 10)
        text(screen, f"{col}: {env.inventory[col]}", x + 30, y, 20)
        y += 24

    y += 18

    text(screen, "Objectives / cards:", x, y, 24)
    y += 34

    for who in (+1, -1):
        text(screen, f"Player {who}", x, y, 22)
        y += 25

        ox = x
        for obj in env.objectives[who]:
            draw_shape_preview(screen, obj, ox, y, scale=24)
            ox += 250

        y += 150

    text(screen, "Move: click source, then target.", x, H - 80, 18)
    text(screen, "Place/Replace: choose color, then click cell.", x, H - 58, 18)
    text(screen, "R = restart, ESC = quit", x, H - 36, 18)


# ============================================================
# BOT SETUP
# ============================================================

def create_bots():
    return {
        "Random": RandomBot(),

        "Heuristic": HeuristicBot(
            max_safety_checks=5,
        ),

        "AlphaBeta-new-d3": NeuralAlphaBetaBot(
            checkpoint_path=str(NEW_CKPT),
            depth=3,
            move_limit=8,
        ),

        "MCTS-old-100": MCTSBot(
            checkpoint_path=str(OLD_CKPT),
            num_sims=100,
        ),

        "MCTS-new-100": MCTSBot(
            checkpoint_path=str(NEW_CKPT),
            num_sims=100,
        ),
    }


def bot_play(bot, env):
    legal = env.legal_moves()

    if not legal:
        return None

    move = bot.choose_move(env)

    if move not in legal:
        print("Bot chose illegal move:", move)
        print("Replacing with first legal move.")
        move = legal[0]

    return move


# ============================================================
# GAME LOOP
# ============================================================

def main():
    pygame.init()

    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Logix: Human vs Bot")

    bots = create_bots()

    if BOT_TO_PLAY_AGAINST not in bots:
        raise ValueError(
            f"Unknown bot '{BOT_TO_PLAY_AGAINST}'. "
            f"Available bots: {list(bots.keys())}"
        )

    bot = bots[BOT_TO_PLAY_AGAINST]

    env = LogixShapeEnv(
        n=7,
        max_game_len=MAX_GAME_LEN,
        seed=None,
    )

    selected_color = "R"
    mode = "place"
    selected_cell = None
    status = "Your move."
    game_over = False

    clock = pygame.time.Clock()

    while True:
        screen.fill(COLORS["bg"])
        draw_board(screen, env, selected_cell)
        draw_panel(screen, env, selected_color, mode, status, BOT_TO_PLAY_AGAINST)
        pygame.display.flip()

        clock.tick(60)

        # ----------------------------
        # BOT MOVE
        # ----------------------------
        if not game_over and env.player == BOT_PLAYER:
            status = "Bot thinking..."

            screen.fill(COLORS["bg"])
            draw_board(screen, env, selected_cell)
            draw_panel(screen, env, selected_color, mode, status, BOT_TO_PLAY_AGAINST)
            pygame.display.flip()

            bot_move = bot_play(bot, env)

            if bot_move is None:
                status = "No legal moves."
                game_over = True
                continue

            _, done, result = env.step(bot_move)

            print("Bot played:", bot_move)
            status = f"Bot played {bot_move}"

            selected_cell = None

            if done:
                game_over = True

                if result == HUMAN_PLAYER:
                    status = "Game over. You won!"
                elif result == BOT_PLAYER:
                    status = "Game over. Bot won!"
                else:
                    status = "Game over. Draw."

                print(status)

            continue

        # ----------------------------
        # EVENTS
        # ----------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

                if event.key == pygame.K_r:
                    env = LogixShapeEnv(
                        n=7,
                        max_game_len=MAX_GAME_LEN,
                        seed=None,
                    )
                    selected_color = "R"
                    mode = "place"
                    selected_cell = None
                    status = "Restarted. Your move."
                    game_over = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if game_over:
                    continue

                if env.player != HUMAN_PLAYER:
                    continue

                mx, my = pygame.mouse.get_pos()

                # ----------------------------
                # PANEL BUTTONS
                # ----------------------------
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

                # ----------------------------
                # BOARD CLICK
                # ----------------------------
                if mx >= SIDE or my >= SIDE:
                    continue

                r = my // CELL
                c = mx // CELL

                if mode == "place":
                    move = ("place", r, c, selected_color)

                elif mode == "replace":
                    move = ("replace", r, c, selected_color)

                elif mode == "move":
                    if selected_cell is None:
                        selected_cell = (r, c)
                        status = f"Selected source {(r, c)}"
                        continue

                    r1, c1 = selected_cell
                    move = ("move", r1, c1, r, c)
                    selected_cell = None

                else:
                    continue

                if move not in env.legal_moves():
                    status = f"Invalid move: {move}"
                    print(status)
                    continue

                _, done, result = env.step(move)

                print("You played:", move)
                status = f"You played {move}"

                if done:
                    game_over = True

                    if result == HUMAN_PLAYER:
                        status = "Game over. You won!"
                    elif result == BOT_PLAYER:
                        status = "Game over. Bot won!"
                    else:
                        status = "Game over. Draw."

                    print(status)


if __name__ == "__main__":
    main()
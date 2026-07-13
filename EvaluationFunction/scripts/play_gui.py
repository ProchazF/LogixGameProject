import pygame, sys, json, os
from datetime import datetime

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from logix_az.env_logix_helper import LogixShapeEnv

CELL = 75
N = 7
SIDE = CELL * N
PANEL_W = 620
W, H = SIDE + PANEL_W, max(SIDE, 920)

COLORS = {
    "bg": (235,235,235), "grid": (40,40,40), "button": (220,220,220),
    "select": (255,150,0), "text": (20,20,20),
    "R": (220,50,50), "G": (60,170,80), "B": (60,100,220),
    "Y": (230,210,60), "Gray": (150,150,150), "Black": (20,20,20),
}
CODE_TO_COLOR = {1:"R",2:"G",3:"B",4:"Y",5:"Gray"}
COLOR_CODE_TO_NAME = {"R": "Red", "G": "Green", "B": "Blue", "Y": "Yellow", "Gray": "Gray"}

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

            cx, cy = c * CELL + CELL//2, r * CELL + CELL//2

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


def draw_shape_preview(screen, obj, x, y, scale=22):
    shape = obj["shape"]
    assigned = obj["assigned_color"]
    allowed = obj["allowed_win_colors"]

    offsets = normalize_shape_offsets(shape.offsets)

    text(screen, shape.name, x, y, 20)
    text(screen, f"not {assigned}", x, y + 20, 18)

    # draw cells
    for dr, dc in offsets:
        rect = pygame.Rect(x + dc * scale, y + 45 + dr * scale, scale - 2, scale - 2)

        # use first allowed color as visual target color
        col = assigned
        pygame.draw.rect(screen, COLORS[col], rect)
        pygame.draw.rect(screen, COLORS["grid"], rect, 1)

        if (dr, dc) == offsets[0]:
            # mark one reference cell, not necessarily black in real game
            pygame.draw.circle(screen, COLORS["Black"], rect.center, 4)


def draw_panel(screen, env, selected_color, mode):
    global buttons
    buttons = []

    x = SIDE + 20
    y = 20

    text(screen, f"Player: {env.player}", x, y); y += 28
    text(screen, f"Turn: {env.turn}", x, y); y += 28
    text(screen, f"Banned: {sorted(env.banned_colors())}", x, y); y += 35

    text(screen, "Mode:", x, y)
    for label, m in [("Place", "place"), ("Move", "move"), ("Replace", "replace")]:
        rect = pygame.Rect(x, y + 28, 110, 36)
        draw_button(screen, rect, label, selected=(mode == m))
        buttons.append((rect, ("mode", m)))
        x += 120
    x = SIDE + 20
    y += 75

    text(screen, "Color:", x, y)
    cx = x
    for col in ("R", "G", "B", "Y", "Gray"):
        rect = pygame.Rect(cx, y + 28, 95, 36)
        draw_button(screen, rect, col, selected=(selected_color == col))
        pygame.draw.circle(screen, COLORS[col], (rect.right - 18, rect.centery), 10)
        buttons.append((rect, ("color", col)))
        cx += 105
    y += 80

    text(screen, "Inventory:", x, y); y += 28
    for col in ("R", "G", "B", "Y", "Gray"):
        pygame.draw.circle(screen, COLORS[col], (x + 12, y + 10), 10)
        text(screen, f"{col}: {env.inventory[col]}", x + 30, y, 20)
        y += 24

    y += 20
    text(screen, "Objectives / cards:", x, y, 24); y += 34

    start_y = y
    for who in (+1, -1):
        text(screen, f"Player {who}", x, y, 22)
        y += 26

        ox = x
        for obj in env.objectives[who]:
            draw_shape_preview(screen, obj, ox, y, scale=24)
            ox += 250

        y += 165

    text(screen, "Controls: click buttons, click board. For move click source then target.", x, H - 60, 18)
    text(screen, "S = save, ESC = quit", x, H - 35, 18)


def serialize_objectives(objectives):
    out = {}
    for who in (+1, -1):
        out[str(who)] = []
        for obj in objectives[who]:
            out[str(who)].append({
                "shape_name": obj["shape"].name,
                "shape_offsets": [list(x) for x in obj["shape"].offsets],
                "assigned_color": obj["assigned_color"],
                "allowed_win_colors": list(obj["allowed_win_colors"]),
            })
    return out


def serialize_initial_state(env):
    return {
        "board": env.board.tolist(),
        "black": env.black.tolist(),
        "player": env.player,
        "turn": env.turn,
        "center": list(env.center),
        "last_colors_played": list(env.last_colors_played),
        "inventory": dict(env.inventory),
        "objectives": serialize_objectives(env.objectives),
        "board_size": env.n,
        "max_game_len": env.max_game_len,
    }


def save_game(initial_state, moves, result=None, finished=False):
    os.makedirs("recorded_games", exist_ok=True)
    path = f"recorded_games/gui_game_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    record = {
        "format_version": 1,
        "created_at": datetime.now().isoformat(),
        "initial_state": initial_state,
        "moves": moves,
        "winner": result,
        "finished": finished,
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)

    print("Saved:", path)


def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Logix GUI Recorder")

    env = LogixShapeEnv(n=7, max_game_len=100, seed=None)

    initial_state = serialize_initial_state(env)

    selected_color = "R"
    mode = "place"
    selected_cell = None
    moves_recorded = []

    while True:
        screen.fill(COLORS["bg"])
        draw_board(screen, env, selected_cell)
        draw_panel(screen, env, selected_color, mode)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                if event.key == pygame.K_s:
                    save_game(initial_state, moves_recorded, result=None, finished=False)

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()

                # panel buttons
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

                # board click
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
                    print("Invalid move:", move)
                    continue

                player_before = env.player
                _, done, result = env.step(move)

                moves_recorded.append({
                    "player": player_before,
                    "move": list(move),
                })

                print("Played:", move)

                if done:
                    print("Game finished. Result:", result)
                    save_game(initial_state, moves_recorded, result=int(result), finished=True)
                    pygame.quit()
                    sys.exit()


if __name__ == "__main__":
    main()
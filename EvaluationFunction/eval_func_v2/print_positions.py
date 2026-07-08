import pygame
import sys
import os
from datetime import datetime

# =========================
# CONFIG
# =========================

CELL = 75
N = 7
BOARD_SIZE = CELL * N

PANEL_H = 170
W = BOARD_SIZE * 2 + 220
H = BOARD_SIZE + PANEL_H

LEFT_BOARD_POS = (40, 70)
RIGHT_BOARD_POS = (BOARD_SIZE + 180, 70)

FPS = 60

COLORS = {
    "bg": (235, 235, 235),
    "grid": (40, 40, 40),
    "text": (20, 20, 20),
    "button": (215, 215, 215),
    "button_active": (255, 180, 70),
    "prev_bg": (245, 245, 245),
    "curr_bg": (255, 255, 255),

    "Red": (220, 50, 50),
    "Green": (60, 170, 80),
    "Blue": (60, 100, 220),
    "Yellow": (230, 210, 60),
    "Gray": (150, 150, 150),
    "Black": (20, 20, 20),
}

MARBLE_COLORS = ["Red", "Green", "Blue", "Yellow", "Gray"]

EMPTY = None
BLACK = "Black"


# =========================
# STATE
# =========================

def empty_board():
    board = [[EMPTY for _ in range(N)] for _ in range(N)]
    board[3][3] = BLACK
    return board


def copy_board(board):
    return [row[:] for row in board]


previous_board = empty_board()
current_board = empty_board()

selected_color = "Red"
mode = "add"      # add / move / replace
selected_cell = None


# =========================
# PYGAME SETUP
# =========================

pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Move Display GUI")
clock = pygame.time.Clock()

font = pygame.font.SysFont(None, 28)
small_font = pygame.font.SysFont(None, 22)


# =========================
# LAYOUT
# =========================

buttons = []


def make_button(label, rect, action):
    buttons.append({
        "label": label,
        "rect": pygame.Rect(rect),
        "action": action
    })


# Color buttons
x = 40
y = BOARD_SIZE + 95
for color in MARBLE_COLORS:
    make_button(color, (x, y, 90, 35), ("color", color))
    x += 100

# Mode buttons
x = 40
y = BOARD_SIZE + 135
make_button("Add", (x, y, 90, 35), ("mode", "add"))
make_button("Move", (x + 100, y, 90, 35), ("mode", "move"))
make_button("Replace", (x + 200, y, 110, 35), ("mode", "replace"))

# Utility buttons
make_button("Save", (W - 270, BOARD_SIZE + 95, 90, 35), ("save", None))
make_button("Undo", (W - 170, BOARD_SIZE + 95, 90, 35), ("undo", None))
make_button("Reset", (W - 270, BOARD_SIZE + 135, 90, 35), ("reset", None))


# =========================
# HELPERS
# =========================

def board_pos_to_cell(mouse_pos, board_pos):
    mx, my = mouse_pos
    bx, by = board_pos

    if not (bx <= mx < bx + BOARD_SIZE and by <= my < by + BOARD_SIZE):
        return None

    col = (mx - bx) // CELL
    row = (my - by) // CELL

    return int(row), int(col)


def save_screenshot():
    os.makedirs("screenshots", exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = f"screenshots/board_state_{timestamp}.png"

    pygame.image.save(screen, path)
    print(f"Saved screenshot: {path}")


def commit_change(new_board):
    global previous_board, current_board

    previous_board = copy_board(current_board)
    current_board = new_board


def reset_boards():
    global previous_board, current_board, selected_cell

    previous_board = empty_board()
    current_board = empty_board()
    selected_cell = None


# =========================
# ACTIONS
# =========================

def add_marble(row, col):
    if current_board[row][col] is not EMPTY:
        return

    new_board = copy_board(current_board)
    new_board[row][col] = selected_color
    commit_change(new_board)


def replace_marble(row, col):
    if current_board[row][col] is EMPTY:
        return

    if current_board[row][col] == BLACK:
        return

    new_board = copy_board(current_board)
    new_board[row][col] = selected_color
    commit_change(new_board)


def move_marble(row, col):
    global selected_cell

    clicked = current_board[row][col]

    if selected_cell is None:
        if clicked is not EMPTY:
            selected_cell = (row, col)
        return

    src_r, src_c = selected_cell

    if (row, col) == selected_cell:
        selected_cell = None
        return

    if current_board[row][col] is not EMPTY:
        selected_cell = (row, col)
        return

    new_board = copy_board(current_board)
    new_board[row][col] = new_board[src_r][src_c]
    new_board[src_r][src_c] = EMPTY

    selected_cell = None
    commit_change(new_board)


def handle_board_click(row, col):
    if mode == "add":
        add_marble(row, col)

    elif mode == "replace":
        replace_marble(row, col)

    elif mode == "move":
        move_marble(row, col)


# =========================
# DRAWING
# =========================

def draw_text(text, x, y, font_obj=font):
    img = font_obj.render(text, True, COLORS["text"])
    screen.blit(img, (x, y))


def draw_board(board, board_pos, title):
    bx, by = board_pos

    pygame.draw.rect(
        screen,
        COLORS["curr_bg"],
        (bx, by, BOARD_SIZE, BOARD_SIZE)
    )

    draw_text(title, bx, by - 35)

    for r in range(N):
        for c in range(N):
            rect = pygame.Rect(
                bx + c * CELL,
                by + r * CELL,
                CELL,
                CELL
            )

            pygame.draw.rect(screen, COLORS["grid"], rect, 2)

            marble = board[r][c]
            if marble is not EMPTY:
                center = rect.center
                radius = CELL // 2 - 10

                pygame.draw.circle(
                    screen,
                    COLORS[marble],
                    center,
                    radius
                )

                pygame.draw.circle(
                    screen,
                    (0, 0, 0),
                    center,
                    radius,
                    2
                )

    if board is current_board and selected_cell is not None:
        r, c = selected_cell
        rect = pygame.Rect(
            bx + c * CELL,
            by + r * CELL,
            CELL,
            CELL
        )
        pygame.draw.rect(screen, (255, 140, 0), rect, 5)


def draw_buttons():
    for button in buttons:
        label = button["label"]
        rect = button["rect"]
        action_type, value = button["action"]

        active = False

        if action_type == "color" and value == selected_color:
            active = True

        if action_type == "mode" and value == mode:
            active = True

        color = COLORS["button_active"] if active else COLORS["button"]

        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, COLORS["grid"], rect, 2)

        text_img = small_font.render(label, True, COLORS["text"])
        text_rect = text_img.get_rect(center=rect.center)
        screen.blit(text_img, text_rect)

def draw_arrow_between_boards():
    start_x = LEFT_BOARD_POS[0] + BOARD_SIZE + 30
    end_x = RIGHT_BOARD_POS[0] - 40
    y = LEFT_BOARD_POS[1] + BOARD_SIZE // 2

    # shaft
    pygame.draw.line(
        screen,
        COLORS["grid"],
        (start_x, y),
        (end_x, y),
        5,
    )

    # arrow head
    pygame.draw.polygon(
        screen,
        COLORS["grid"],
        [
            (end_x + 18, y),      # tip
            (end_x - 10, y - 14),
            (end_x - 10, y + 14),
        ],
    )


def draw_ui():
    screen.fill(COLORS["bg"])

    draw_board(previous_board, LEFT_BOARD_POS, "Previous position")
    draw_board(current_board, RIGHT_BOARD_POS, "Current position")

    draw_buttons()

    draw_text(f"Selected color: {selected_color}", 520, BOARD_SIZE + 95, small_font)
    draw_text(f"Mode: {mode}", 520, BOARD_SIZE + 125, small_font)

    draw_board(previous_board, LEFT_BOARD_POS, "Previous position")
    draw_arrow_between_boards()
    draw_board(current_board, RIGHT_BOARD_POS, "Current position")



# =========================
# MAIN LOOP
# =========================

running = True

while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()

            clicked_button = False

            for button in buttons:
                if button["rect"].collidepoint(mouse_pos):
                    action_type, value = button["action"]

                    if action_type == "color":
                        selected_color = value

                    elif action_type == "mode":
                        mode = value
                        selected_cell = None

                    elif action_type == "save":
                        save_screenshot()

                    elif action_type == "undo":
                        current_board = copy_board(previous_board)
                        selected_cell = None

                    elif action_type == "reset":
                        reset_boards()

                    clicked_button = True
                    break

            if clicked_button:
                continue

            cell = board_pos_to_cell(mouse_pos, RIGHT_BOARD_POS)

            if cell is not None:
                row, col = cell
                handle_board_click(row, col)

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                save_screenshot()

            elif event.key == pygame.K_r:
                reset_boards()

            elif event.key == pygame.K_1:
                mode = "add"
                selected_cell = None

            elif event.key == pygame.K_2:
                mode = "move"
                selected_cell = None

            elif event.key == pygame.K_3:
                mode = "replace"
                selected_cell = None

    draw_ui()
    pygame.display.flip()

pygame.quit()
sys.exit()
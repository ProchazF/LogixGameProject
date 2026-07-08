import random
import pygame

from logix_az.env_logix_helper import ALL_SHAPES

CELL = 40
CARD_W = 280
CARD_H = 280
COLS = 6
ROWS = 3

W = COLS * CARD_W
H = ROWS * CARD_H

COLORS = [
    (220, 50, 50),    # red
    (60, 170, 80),    # green
    (60, 100, 220),   # blue
    (230, 210, 60),   # yellow
]


def normalize_offsets(offsets):
    min_r = min(r for r, c in offsets)
    min_c = min(c for r, c in offsets)
    return [(r - min_r, c - min_c) for r, c in offsets]


def draw_shape(screen, shape, x, y, color):
    offsets = normalize_offsets(shape.offsets)

    # Bounding box of the normalized shape
    max_r = max(r for r, c in offsets)
    max_c = max(c for r, c in offsets)

    shape_w = (max_c + 1) * CELL
    shape_h = (max_r + 1) * CELL

    # Slightly left and lower than before
    shape_x = x + (CARD_W - shape_w) // 2 - 15
    shape_y = y + 45

    # Draw squares
    for r, c in offsets:
        rect = pygame.Rect(
            shape_x + c * CELL,
            shape_y + r * CELL,
            CELL - 2,
            CELL - 2,
        )
        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, (0, 0, 0), rect, 2)

    # Label in the top-left corner
    font = pygame.font.SysFont(None, 24)
    label = font.render(shape.name, True, (20, 20, 20))

    screen.blit(label, (x, y))

def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("All Logix Shapes")

    screen.fill((245, 245, 245))

    random.seed()

    for i, shape in enumerate(ALL_SHAPES):
        row = i // COLS
        col = i % COLS

        x = col * CARD_W + 20
        y = row * CARD_H + 20

        color = random.choice(COLORS)

        pygame.draw.rect(
            screen,
            (230, 230, 230),
            pygame.Rect(col * CARD_W + 8, row * CARD_H + 8, CARD_W - 16, CARD_H - 16),
            border_radius=8,
        )

        draw_shape(screen, shape, x, y, color)

    pygame.display.flip()

    pygame.image.save(screen, "all_shapes.png")
    print("Saved image as all_shapes.png")

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

    pygame.quit()


if __name__ == "__main__":
    main()
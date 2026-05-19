import sys
import pygame
from constants import WIDTH, HEIGHT
from game import GameScreen

BLACK  = (  0,   0,   0)
YELLOW = (255, 220,   0)
TEAL   = (  0, 200, 200)


def run_title_screen(screen, clock):
    font_title = pygame.font.SysFont("monospace", 72, bold=True)
    font_sub   = pygame.font.SysFont("monospace", 24)

    blink_timer = 0
    show_prompt = True

    while True:
        dt = clock.tick(60)
        blink_timer += dt
        if blink_timer >= 500:
            blink_timer = 0
            show_prompt = not show_prompt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                return

        screen.fill(BLACK)

        title_surf = font_title.render("BOULDERDASH", True, YELLOW)
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 3)))

        if show_prompt:
            sub_surf = font_sub.render("PRESS SPACE TO START", True, TEAL)
            screen.blit(sub_surf, sub_surf.get_rect(center=(WIDTH // 2, HEIGHT * 2 // 3)))

        pygame.display.flip()


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Boulderdash")
    clock = pygame.time.Clock()

    run_title_screen(screen, clock)
    GameScreen(screen, clock).run()

    pygame.quit()


if __name__ == "__main__":
    main()

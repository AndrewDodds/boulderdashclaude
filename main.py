import sys
import os
import glob
import pygame
from constants import WIDTH, HEIGHT
from game import GameScreen
from designer import LevelDesigner

BLACK  = (  0,   0,   0)
YELLOW = (255, 220,   0)
TEAL   = (  0, 200, 200)
RED    = (255,  80,  80)


def run_title_screen(screen, clock):
    font_title  = pygame.font.SysFont("monospace", 72, bold=True)
    font_option = pygame.font.SysFont("monospace", 30)

    while True:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r: return 'random'
                if event.key == pygame.K_f: return 'files'
                if event.key == pygame.K_d: return 'designer'

        screen.fill(BLACK)

        title = font_title.render("BOULDERDASH", True, YELLOW)
        screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 3)))

        cy = HEIGHT * 2 // 3
        for text, offset in [
            ("[R]  Random Level",   -44),
            ("[F]  File Levels",      0),
            ("[D]  Level Designer",  44),
        ]:
            surf = font_option.render(text, True, TEAL)
            screen.blit(surf, surf.get_rect(center=(WIDTH // 2, cy + offset)))

        pygame.display.flip()


def show_message(screen, clock, text, colour=RED, duration_ms=2500):
    font = pygame.font.SysFont("monospace", 32, bold=True)
    surf = font.render(text, True, colour)
    deadline = pygame.time.get_ticks() + duration_ms
    while pygame.time.get_ticks() < deadline:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                return
        screen.fill(BLACK)
        screen.blit(surf, surf.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
        pygame.display.flip()


def get_level_files():
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "levels")
    return sorted(glob.glob(os.path.join(base, "*.txt")))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Boulderdash")
    clock = pygame.time.Clock()

    while True:
        mode = run_title_screen(screen, clock)

        if mode == 'random':
            GameScreen(screen, clock).run()

        elif mode == 'files':
            level_files = get_level_files()
            if not level_files:
                show_message(screen, clock, "No level files found in levels/")
                continue
            for level_path in level_files:
                result = GameScreen(screen, clock, level_path=level_path).run()
                if result != 'won':
                    break
            else:
                show_message(screen, clock, "All levels complete!", colour=YELLOW)

        elif mode == 'designer':
            LevelDesigner(screen, clock).run()
            pygame.key.set_repeat(0)  # reset so title screen isn't flooded


if __name__ == "__main__":
    main()

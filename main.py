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
GREY   = (120, 120, 120)

NUM_CHAPTERS = 3
LEVELS_PER_CHAPTER = 5


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
            ("[F]  Play Levels",      0),
            ("[D]  Level Designer",  44),
        ]:
            surf = font_option.render(text, True, TEAL)
            screen.blit(surf, surf.get_rect(center=(WIDTH // 2, cy + offset)))

        pygame.display.flip()


def run_chapter_select(screen, clock, chapters):
    font_title  = pygame.font.SysFont("monospace", 48, bold=True)
    font_item   = pygame.font.SysFont("monospace", 32)
    font_hint   = pygame.font.SysFont("monospace", 18)
    selected    = 0

    while True:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % NUM_CHAPTERS
                if event.key == pygame.K_DOWN:
                    selected = (selected + 1) % NUM_CHAPTERS
                if event.key == pygame.K_RETURN:
                    if chapters[selected]:
                        return selected

        screen.fill(BLACK)

        title = font_title.render("Select Chapter", True, YELLOW)
        screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 4)))

        cy = HEIGHT // 2
        for i, files in enumerate(chapters):
            count  = len(files)
            label  = f"Chapter {i + 1}   {count}/{LEVELS_PER_CHAPTER} levels"
            if count == 0:
                colour = GREY
            elif i == selected:
                colour = YELLOW
            else:
                colour = TEAL
            surf = font_item.render(label, True, colour)
            rect = surf.get_rect(center=(WIDTH // 2, cy + i * 52))
            screen.blit(surf, rect)
            if i == selected and count > 0:
                arrow = font_item.render(">", True, YELLOW)
                screen.blit(arrow, (rect.left - 30, rect.top))

        hint = font_hint.render("↑↓ = choose   Enter = play   Esc = back", True, GREY)
        screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT * 7 // 8)))
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


def get_chapters():
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "levels")
    chapters = []
    for i in range(1, NUM_CHAPTERS + 1):
        chapter_dir = os.path.join(base, f"chapter{i}")
        files = sorted(glob.glob(os.path.join(chapter_dir, "level*.txt")))
        chapters.append(files)
    return chapters


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
            chapters = get_chapters()
            chapter_idx = run_chapter_select(screen, clock, chapters)
            if chapter_idx is None:
                continue
            level_files = chapters[chapter_idx]
            for level_path in level_files:
                result = GameScreen(screen, clock, level_path=level_path).run()
                if result != 'won':
                    break
            else:
                show_message(screen, clock,
                             f"Chapter {chapter_idx + 1} complete!", colour=YELLOW)

        elif mode == 'designer':
            LevelDesigner(screen, clock).run()
            pygame.key.set_repeat(0)


if __name__ == "__main__":
    main()

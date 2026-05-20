import sys
import os
import math
import glob
import random
import pygame
from constants import TILE_SIZE, COLS, ROWS, WIDTH, HEIGHT
from tile import Tile
from tiles import load_sheet, TILE_CLASSES, PlayerTile, Enemy1Tile, Enemy2Tile
from level import Level

_SHEETS = {
    "blue":  "images/bd_blue_big.png",
    "red":   "images/bd_red_big.png",
    "green": "images/bd_green_big.png",
}
CAM_SPEED  = 8.0
ANIM_MS    = 250
PALETTE_H  = TILE_SIZE + 22   # sprite row + key-label row
BLACK      = (0, 0, 0)
YELLOW     = (255, 220, 0)

# (key-label, display-name, value)
# value is a Tile enum or a string sentinel for non-tile entities
PALETTE = [
    ("1", "Empty",   Tile.EMPTY),
    ("2", "Dirt",    Tile.DIRT),
    ("3", "Wall",    Tile.WALL),
    ("4", "Boulder", Tile.BOULDER),
    ("5", "Diamond", Tile.DIAMOND),
    ("6", "Exit",    Tile.EXIT),
    ("7", "Slime",   Tile.SLIME),
    ("8", "Player",  "player"),
    ("9", "D.Enemy", "d_enemy"),
    ("0", "X.Enemy", "x_enemy"),
]

_NUM_KEYS = {
    pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2,
    pygame.K_4: 3, pygame.K_5: 4, pygame.K_6: 5,
    pygame.K_7: 6, pygame.K_8: 7, pygame.K_9: 8, pygame.K_0: 9,
}

ARROW_KEYS = {
    pygame.K_LEFT: (-1, 0), pygame.K_RIGHT: (1, 0),
    pygame.K_UP:   (0, -1), pygame.K_DOWN:  (0, 1),
}


class LevelDesigner:
    def __init__(self, screen, clock, level_path=None):
        self.screen = screen
        self.clock  = clock
        if level_path and os.path.exists(level_path):
            self.level     = Level.from_file(level_path)
            self.save_path = level_path
        else:
            self.level     = self._blank_level()
            self.save_path = self._next_path()

        load_sheet(_SHEETS[self.level.colour])

        self.cursor_x, self.cursor_y = self.level.player_start
        self.selected   = 0
        self.cam_x, self.cam_y = self._camera_target()
        self.anim_frame = 0
        self.anim_timer = 0

        self._fsm = pygame.font.SysFont("monospace", 13, bold=True)
        self._fmd = pygame.font.SysFont("monospace", 18, bold=True)
        self._flg = pygame.font.SysFont("monospace", 22, bold=True)
        pygame.key.set_repeat(150, 80)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _blank_level():
        from constants import LEVEL_W, LEVEL_H
        lv = Level()
        for x in range(LEVEL_W):
            lv.tiles[0][x]            = Tile.WALL
            lv.tiles[LEVEL_H - 1][x]  = Tile.WALL
        for y in range(LEVEL_H):
            lv.tiles[y][0]            = Tile.WALL
            lv.tiles[y][LEVEL_W - 1]  = Tile.WALL
        for y in range(1, LEVEL_H - 1):
            for x in range(1, LEVEL_W - 1):
                lv.tiles[y][x] = Tile.DIRT
        lv.tiles[LEVEL_H - 2][LEVEL_W - 2] = Tile.EXIT
        lv.player_start = (1, 1)
        return lv

    @staticmethod
    def _next_path():
        base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "levels")
        os.makedirs(base, exist_ok=True)
        n = len(glob.glob(os.path.join(base, "level*.txt"))) + 1
        return os.path.join(base, f"level{n}.txt")

    # ------------------------------------------------------------------
    # Camera
    # ------------------------------------------------------------------

    def _camera_target(self):
        view_h = HEIGHT - PALETTE_H
        tx = self.cursor_x * TILE_SIZE - WIDTH  // 2 + TILE_SIZE // 2
        ty = self.cursor_y * TILE_SIZE - view_h // 2 + TILE_SIZE // 2
        max_tx = max(0, self.level.width  * TILE_SIZE - WIDTH)
        max_ty = max(0, self.level.height * TILE_SIZE - view_h)
        return float(max(0, min(tx, max_tx))), float(max(0, min(ty, max_ty)))

    def _update_camera(self, dt):
        tx, ty = self._camera_target()
        f = 1.0 - math.exp(-CAM_SPEED * dt / 1000.0)
        self.cam_x += (tx - self.cam_x) * f
        self.cam_y += (ty - self.cam_y) * f

    # ------------------------------------------------------------------
    # Placement
    # ------------------------------------------------------------------

    def _place_at(self, x, y):
        _, _, item = PALETTE[self.selected]
        if isinstance(item, Tile):
            self.level.tiles[y][x] = item
            self.level.enemy_spawns = [
                s for s in self.level.enemy_spawns if (s[0], s[1]) != (x, y)
            ]
        elif item == "player":
            self.level.player_start = (x, y)
        else:
            etype = "diamond" if item == "d_enemy" else "explosive"
            self.level.tiles[y][x] = Tile.EMPTY
            self.level.enemy_spawns = [
                s for s in self.level.enemy_spawns if (s[0], s[1]) != (x, y)
            ]
            self.level.enemy_spawns.append((x, y, etype))

    def _place(self):
        self._place_at(self.cursor_x, self.cursor_y)

    def _scatter(self, count=20):
        interior = [(x, y)
                    for x in range(1, self.level.width  - 1)
                    for y in range(1, self.level.height - 1)]
        for x, y in random.sample(interior, min(count, len(interior))):
            self._place_at(x, y)

    def _stamp_3x3(self):
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                x = self.cursor_x + dx
                y = self.cursor_y + dy
                if 0 <= x < self.level.width and 0 <= y < self.level.height:
                    self._place_at(x, y)

    # ------------------------------------------------------------------
    # Dialogs
    # ------------------------------------------------------------------

    def _dialog_backdrop(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, 0))
        bw, bh = 530, 115
        bx, by = (WIDTH - bw) // 2, (HEIGHT - bh) // 2
        pygame.draw.rect(self.screen, (20, 20, 50),  (bx, by, bw, bh))
        pygame.draw.rect(self.screen, (80, 80, 200), (bx, by, bw, bh), 2)
        return bx, by

    def _run_save_dialog(self):
        text = self.save_path
        while True:
            self.clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        try:
                            d = os.path.dirname(text)
                            if d:
                                os.makedirs(d, exist_ok=True)
                            self.level.save_to_file(text)
                            self.save_path = text
                            return True
                        except OSError:
                            pass
                    elif event.key == pygame.K_ESCAPE:
                        return False
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    elif event.unicode and event.unicode.isprintable():
                        text += event.unicode

            bx, by = self._dialog_backdrop()
            self.screen.blit(self._flg.render("Save level as:",         True, YELLOW),       (bx+12, by+8))
            self.screen.blit(self._fmd.render(text + "|",               True, (255,255,255)), (bx+12, by+44))
            self.screen.blit(self._fsm.render("Enter = save  Esc = cancel", True, (150,150,150)), (bx+12, by+86))
            pygame.display.flip()

    def _run_exit_dialog(self):
        while True:
            self.clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key   == pygame.K_y:      return 'save'
                    elif event.key == pygame.K_n:      return 'discard'
                    elif event.key == pygame.K_ESCAPE: return 'cancel'

            bx, by = self._dialog_backdrop()
            self.screen.blit(self._flg.render("Save before exiting?",                    True, YELLOW),      (bx+12, by+8))
            self.screen.blit(self._fsm.render("[Y] Save   [N] Discard   [Esc] Cancel",  True, (0,220,220)),  (bx+12, by+52))
            pygame.display.flip()

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _draw(self):
        view_h = HEIGHT - PALETTE_H

        # Clip tile rendering to the view area so it never bleeds into the palette bar
        self.screen.set_clip(pygame.Rect(0, 0, WIDTH, view_h))

        first_col = math.floor(self.cam_x / TILE_SIZE)
        first_row = math.floor(self.cam_y / TILE_SIZE)
        off_x     = -(self.cam_x - first_col * TILE_SIZE)
        off_y     = -(self.cam_y - first_row * TILE_SIZE)

        for row in range(ROWS + 1):
            ty = first_row + row
            if not (0 <= ty < self.level.height):
                continue
            for col in range(COLS + 1):
                tx = first_col + col
                if not (0 <= tx < self.level.width):
                    continue
                self.screen.blit(
                    TILE_CLASSES[self.level.tiles[ty][tx]].sprite(self.anim_frame),
                    (int(off_x + col * TILE_SIZE), int(off_y + row * TILE_SIZE)),
                )

        # Enemy spawns — shown with actual sprites
        for ex, ey, etype in self.level.enemy_spawns:
            cls = Enemy1Tile if etype == "diamond" else Enemy2Tile
            self.screen.blit(cls.sprite(self.anim_frame),
                             (int(ex * TILE_SIZE - self.cam_x),
                              int(ey * TILE_SIZE - self.cam_y)))

        # Player start — shown with player sprite
        px, py = self.level.player_start
        self.screen.blit(PlayerTile.sprite(self.anim_frame),
                         (int(px * TILE_SIZE - self.cam_x),
                          int(py * TILE_SIZE - self.cam_y)))

        # Cursor highlight
        pygame.draw.rect(
            self.screen, YELLOW,
            (int(self.cursor_x * TILE_SIZE - self.cam_x),
             int(self.cursor_y * TILE_SIZE - self.cam_y),
             TILE_SIZE, TILE_SIZE), 3,
        )

        self.screen.set_clip(None)
        self._draw_palette(view_h)
        self._draw_hud()

    def _draw_palette(self, bar_y):
        bar = pygame.Surface((WIDTH, PALETTE_H), pygame.SRCALPHA)
        bar.fill((0, 0, 0, 210))
        self.screen.blit(bar, (0, bar_y))

        slot_w = WIDTH // len(PALETTE)
        for i, (key, name, item) in enumerate(PALETTE):
            x0 = i * slot_w
            cx = x0 + slot_w // 2
            if i == self.selected:
                pygame.draw.rect(self.screen, (70, 70, 10),
                                 (x0+2, bar_y+2, slot_w-4, PALETTE_H-4))
                pygame.draw.rect(self.screen, YELLOW,
                                 (x0+2, bar_y+2, slot_w-4, PALETTE_H-4), 1)

            if isinstance(item, Tile):
                spr = TILE_CLASSES[item].sprite(self.anim_frame)
            elif item == "player":
                spr = PlayerTile.sprite(self.anim_frame)
            elif item == "d_enemy":
                spr = Enemy1Tile.sprite(self.anim_frame)
            else:
                spr = Enemy2Tile.sprite(self.anim_frame)
            self.screen.blit(spr, spr.get_rect(centerx=cx, top=bar_y + 2))

            lbl = self._fsm.render(f"{key}:{name}", True, (200, 200, 200))
            self.screen.blit(lbl, lbl.get_rect(centerx=cx, top=bar_y + TILE_SIZE + 5))

    def _draw_hud(self):
        colour_label = {"blue": "Blue [B]", "red": "Red [R]", "green": "Green [G]"}
        txt  = (f"Diamonds: {self.level.diamonds_required} [+/-]"
                f"    Colour: {colour_label[self.level.colour]}")
        surf = self._fsm.render(txt, True, YELLOW)
        pad  = 4
        bg   = pygame.Surface((surf.get_width() + pad*2, surf.get_height() + pad*2),
                               pygame.SRCALPHA)
        bg.fill((0, 0, 0, 180))
        self.screen.blit(bg,   (0, 0))
        self.screen.blit(surf, (pad, pad))

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self):
        while True:
            dt = self.clock.tick(60)
            self._update_camera(dt)

            self.anim_timer += dt
            if self.anim_timer >= ANIM_MS:
                self.anim_timer = 0
                self.anim_frame = (self.anim_frame + 1) % 28

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        action = self._run_exit_dialog()
                        if action == 'save':
                            self._run_save_dialog()
                            return
                        elif action == 'discard':
                            return
                        # 'cancel' → keep editing

                    elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                        self._run_save_dialog()

                    elif event.key in _NUM_KEYS:
                        self.selected = _NUM_KEYS[event.key]

                    elif event.key in ARROW_KEYS:
                        dx, dy = ARROW_KEYS[event.key]
                        self.cursor_x = max(0, min(self.cursor_x + dx, self.level.width  - 1))
                        self.cursor_y = max(0, min(self.cursor_y + dy, self.level.height - 1))

                    elif event.key == pygame.K_SPACE:
                        self._place()
                    elif event.key == pygame.K_RETURN:
                        self._scatter()
                    elif event.key == pygame.K_TAB:
                        self._stamp_3x3()

                    elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                        self.level.diamonds_required += 1
                    elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                        self.level.diamonds_required = max(1, self.level.diamonds_required - 1)

                    elif event.key in (pygame.K_b, pygame.K_r, pygame.K_g):
                        new = {pygame.K_b: "blue", pygame.K_r: "red", pygame.K_g: "green"}[event.key]
                        if new != self.level.colour:
                            self.level.colour = new
                            load_sheet(_SHEETS[new])

            self._draw()
            pygame.display.flip()

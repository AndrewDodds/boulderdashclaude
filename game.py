import math
import random
import sys
import pygame
from constants import TILE_SIZE, COLS, ROWS, WIDTH, HEIGHT
from tile import Tile
from tiles import load_sheet, TILE_CLASSES, PlayerTile, ExplosionTile, DiamondTile
from entities import DiamondEnemy, ExplosiveEnemy
from level import Level

SHEET_BLUE  = "images/bd_blue_big.png"
SHEET_RED   = "images/bd_red_big.png"
SHEET_GREEN = "images/bd_green_big.png"

ANIM_MS      = 250   # ms per animation frame
PHYSICS_MS   = 200   # ms per physics step
CAM_SPEED    = 8.0   # exponential lerp rate (higher = snappier)


ARROW_KEYS = {
    pygame.K_LEFT:  (-1,  0),
    pygame.K_RIGHT: ( 1,  0),
    pygame.K_UP:    ( 0, -1),
    pygame.K_DOWN:  ( 0,  1),
}


class Player:
    def __init__(self, x, y):
        self.x     = x
        self.y     = y
        self.alive = True


class GameScreen:
    def __init__(self, screen, clock, sheet=SHEET_BLUE):
        self.screen = screen
        self.clock  = clock
        load_sheet(sheet)
        self.level              = Level()
        self.player             = Player(*self.level.player_start)
        self.diamonds_collected = 0
        self.level_complete     = False
        self.anim_frame         = 0
        self.anim_timer         = 0
        self.physics_timer      = 0
        self.enemies = [
            DiamondEnemy(x, y) if t == "diamond" else ExplosiveEnemy(x, y)
            for x, y, t in self.level.enemy_spawns
        ]
        # Enemies live in empty space — clear any tile they spawn on
        for enemy in self.enemies:
            self.level.tiles[enemy.y][enemy.x] = Tile.EMPTY
        self.falling: set[tuple[int, int]] = set()         # boulder positions that were falling last tick
        self.explosions: dict[tuple[int, int], int] = {}   # pos -> current frame
        # Initialise camera at target so it doesn't sweep in from the corner
        self.cam_x, self.cam_y  = self._camera_target()
        self._hud_font = pygame.font.SysFont("monospace", 18, bold=True)
        pygame.key.set_repeat(150, 100)

    # ------------------------------------------------------------------
    # Camera
    # ------------------------------------------------------------------

    def _camera_target(self):
        tx = self.player.x * TILE_SIZE - WIDTH  // 2 + TILE_SIZE // 2
        ty = self.player.y * TILE_SIZE - HEIGHT // 2 + TILE_SIZE // 2
        tx = max(0, min(tx, self.level.width  * TILE_SIZE - WIDTH))
        ty = max(0, min(ty, self.level.height * TILE_SIZE - HEIGHT))
        return float(tx), float(ty)

    def _update_camera(self, dt):
        tx, ty  = self._camera_target()
        factor  = 1.0 - math.exp(-CAM_SPEED * dt / 1000.0)
        self.cam_x += (tx - self.cam_x) * factor
        self.cam_y += (ty - self.cam_y) * factor

    # ------------------------------------------------------------------
    # Game logic
    # ------------------------------------------------------------------

    def _try_move(self, dx, dy):
        nx   = self.player.x + dx
        ny   = self.player.y + dy
        tile = self.level.tiles[ny][nx]

        if tile == Tile.BOULDER:
            # Can only push sideways, and only into an empty tile
            if dy != 0 or self.level.tiles[ny][nx + dx] != Tile.EMPTY:
                return
            self.level.tiles[ny][nx + dx] = Tile.BOULDER
            self.level.tiles[ny][nx]      = Tile.EMPTY

        elif tile in (Tile.WALL, Tile.EXIT):
            return

        if tile == Tile.DIRT:
            self.level.tiles[ny][nx] = Tile.EMPTY
        elif tile == Tile.DIAMOND:
            self.level.tiles[ny][nx] = Tile.EMPTY
            self.diamonds_collected  += 1
            if self.diamonds_collected >= self.level.diamonds_required:
                self._open_exit()

        self.player.x = nx
        self.player.y = ny

        if self.level.tiles[ny][nx] == Tile.OPENEXIT:
            self.level_complete = True

        if self._enemy_at(nx, ny) is not None:
            self.player.alive = False
            self._trigger_explosion(self.player.x, self.player.y)

    def _enemy_at(self, x, y):
        for enemy in self.enemies:
            if enemy.alive and enemy.x == x and enemy.y == y:
                return enemy
        return None

    def _physics_step(self):
        tiles       = self.level.tiles
        moved       = set()
        new_falling = set()
        ROUNDED     = {Tile.BOULDER, Tile.DIAMOND}

        for y in range(self.level.height - 2, 0, -1):
            for x in range(1, self.level.width - 1):
                tile = tiles[y][x]
                if (x, y) in moved or tile not in ROUNDED:
                    continue

                below = tiles[y + 1][x]

                if below == Tile.EMPTY:
                    was_falling = (x, y) in self.falling

                    # A stationary tile is supported by the player standing beneath it
                    if not was_falling and x == self.player.x and y + 1 == self.player.y:
                        continue

                    tiles[y][x]     = Tile.EMPTY
                    tiles[y + 1][x] = tile
                    moved.add((x, y + 1))
                    new_falling.add((x, y + 1))

                    # Boulder kills any enemy it lands on
                    hit = self._enemy_at(x, y + 1)
                    if hit is not None:
                        hit.alive = False
                        self._trigger_explosion(hit.x, hit.y, hit.diamond_explosion)

                    # Only lethal to player if the tile was already in motion last tick
                    if was_falling and x == self.player.x and y + 1 == self.player.y:
                        self.player.alive = False
                        self._trigger_explosion(self.player.x, self.player.y)

                elif below in ROUNDED:
                    if (tiles[y][x - 1] == Tile.EMPTY and
                            tiles[y + 1][x - 1] == Tile.EMPTY and
                            not (self.player.x == x - 1 and self.player.y == y) and
                            not (self.player.x == x - 1 and self.player.y == y + 1)):
                        tiles[y][x]     = Tile.EMPTY
                        tiles[y][x - 1] = tile
                        moved.add((x - 1, y))
                    elif (tiles[y][x + 1] == Tile.EMPTY and
                            tiles[y + 1][x + 1] == Tile.EMPTY and
                            not (self.player.x == x + 1 and self.player.y == y) and
                            not (self.player.x == x + 1 and self.player.y == y + 1)):
                        tiles[y][x]     = Tile.EMPTY
                        tiles[y][x + 1] = tile
                        moved.add((x + 1, y))

        self.falling = new_falling
        self._update_explosions()
        self._slime_step()

        occupied = {(e.x, e.y) for e in self.enemies if e.alive}
        for enemy in self.enemies:
            if enemy.alive:
                occupied.discard((enemy.x, enemy.y))
                enemy.update(self.level.tiles, occupied)
                occupied.add((enemy.x, enemy.y))
                if enemy.x == self.player.x and enemy.y == self.player.y:
                    self.player.alive = False
                    self._trigger_explosion(self.player.x, self.player.y)

    def _trigger_explosion(self, cx, cy, leave_diamonds=False):
        fill = Tile.DIAMOND if leave_diamonds else Tile.EMPTY
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                x, y = cx + dx, cy + dy
                if 1 <= x < self.level.width - 1 and 1 <= y < self.level.height - 1:
                    if self.level.tiles[y][x] != Tile.WALL:
                        self.level.tiles[y][x] = fill
                        self.explosions[(x, y)] = 0
                    hit = self._enemy_at(x, y)
                    if hit is not None:
                        hit.alive = False

    def _slime_step(self):
        tiles   = self.level.tiles
        IMMUNE  = {Tile.WALL, Tile.BOULDER, Tile.DIAMOND,
                   Tile.EXIT, Tile.OPENEXIT, Tile.SLIME}
        SPREADS = {Tile.EMPTY, Tile.DIRT}

        slime_cells = [
            (x, y)
            for y in range(1, self.level.height - 1)
            for x in range(1, self.level.width  - 1)
            if tiles[y][x] == Tile.SLIME
        ]

        for sx, sy in slime_cells:
            for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
                nx, ny = sx + dx, sy + dy

                if self.player.alive and nx == self.player.x and ny == self.player.y:
                    self.player.alive = False
                    self._trigger_explosion(nx, ny)
                    continue

                hit = self._enemy_at(nx, ny)
                if hit is not None:
                    hit.alive = False
                    self._trigger_explosion(nx, ny, hit.diamond_explosion)
                    continue

                if tiles[ny][nx] in SPREADS and random.random() < 0.02:
                    tiles[ny][nx] = Tile.SLIME

    def _update_explosions(self):
        finished = [pos for pos, frame in self.explosions.items()
                    if frame >= ExplosionTile.frame_count() - 1]
        for pos in finished:
            del self.explosions[pos]
        for pos in self.explosions:
            self.explosions[pos] += 1

    def _open_exit(self):
        for y in range(self.level.height):
            for x in range(self.level.width):
                if self.level.tiles[y][x] == Tile.EXIT:
                    self.level.tiles[y][x] = Tile.OPENEXIT

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _draw(self):
        first_col = math.floor(self.cam_x / TILE_SIZE)
        first_row = math.floor(self.cam_y / TILE_SIZE)
        offset_x  = -(self.cam_x - first_col * TILE_SIZE)
        offset_y  = -(self.cam_y - first_row * TILE_SIZE)

        for row in range(ROWS + 1):
            ty = first_row + row
            if not (0 <= ty < self.level.height):
                continue
            for col in range(COLS + 1):
                tx = first_col + col
                if not (0 <= tx < self.level.width):
                    continue
                tile_cls = TILE_CLASSES[self.level.tiles[ty][tx]]
                self.screen.blit(
                    tile_cls.sprite(self.anim_frame),
                    (int(offset_x + col * TILE_SIZE), int(offset_y + row * TILE_SIZE)),
                )

        for enemy in self.enemies:
            if enemy.alive:
                ex = int(enemy.x * TILE_SIZE - self.cam_x)
                ey = int(enemy.y * TILE_SIZE - self.cam_y)
                self.screen.blit(enemy.sprite(self.anim_frame), (ex, ey))

        if self.player.alive:
            px = int(self.player.x * TILE_SIZE - self.cam_x)
            py = int(self.player.y * TILE_SIZE - self.cam_y)
            self.screen.blit(PlayerTile.sprite(self.anim_frame), (px, py))

        for (tx, ty), frame in self.explosions.items():
            sx = int(tx * TILE_SIZE - self.cam_x)
            sy = int(ty * TILE_SIZE - self.cam_y)
            self.screen.blit(ExplosionTile.sprite(frame), (sx, sy))

        self._draw_hud()

    def _draw_hud(self):
        icon   = DiamondTile.sprite(self.anim_frame)
        needed = self.level.diamonds_required
        label  = f"{self.diamonds_collected} / {needed}"
        text   = self._hud_font.render(label, True, (255, 220, 0))

        pad = 6
        bar_h = TILE_SIZE + pad * 2
        bar_w = pad + TILE_SIZE + pad + text.get_width() + pad

        bar = pygame.Surface((bar_w, bar_h), pygame.SRCALPHA)
        bar.fill((0, 0, 0, 160))
        self.screen.blit(bar, (0, 0))

        self.screen.blit(icon, (pad, pad))
        self.screen.blit(text, (pad + TILE_SIZE + pad,
                                pad + (TILE_SIZE - text.get_height()) // 2))

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

            self.physics_timer += dt
            if self.physics_timer >= PHYSICS_MS:
                self.physics_timer -= PHYSICS_MS
                self._physics_step()
                if not self.player.alive and not self.explosions:
                    return
            if self.level_complete:
                return

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return
                    if event.key in ARROW_KEYS:
                        self._try_move(*ARROW_KEYS[event.key])

            self._draw()
            pygame.display.flip()

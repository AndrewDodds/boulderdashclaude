import random
from tile import Tile
from constants import LEVEL_W, LEVEL_H


class Level:
    def __init__(self):
        self.width    = LEVEL_W
        self.height   = LEVEL_H
        self.tiles    = [[Tile.EMPTY] * LEVEL_W for _ in range(LEVEL_H)]
        self.player_start        = (2, 2)   # (x, y)
        self.diamonds_required   = 10
        self.enemy_spawns: list[tuple[int, int, str]] = []  # (x, y, type)
        self._build_test_level()

    # tiles[y][x] throughout
    def _build_test_level(self):
        # Impassable border
        for x in range(self.width):
            self.tiles[0][x]                = Tile.WALL
            self.tiles[self.height - 1][x]  = Tile.WALL
        for y in range(self.height):
            self.tiles[y][0]                = Tile.WALL
            self.tiles[y][self.width - 1]   = Tile.WALL

        # Interior filled with dirt
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                self.tiles[y][x] = Tile.DIRT

        rng = random.Random(42)

        # Carve open pockets before placing objects
        for _ in range(8):
            cx = rng.randint(2, self.width  - 3)
            cy = rng.randint(2, self.height - 3)
            w  = rng.randint(2, 5)
            h  = rng.randint(2, 4)
            for dy in range(h):
                for dx in range(w):
                    nx, ny = cx + dx, cy + dy
                    if 1 <= nx < self.width - 1 and 1 <= ny < self.height - 1:
                        self.tiles[ny][nx] = Tile.EMPTY

        for _ in range(30):
            x, y = rng.randint(2, self.width - 2), rng.randint(2, self.height - 2)
            self.tiles[y][x] = Tile.BOULDER
        for _ in range(20):
            x, y = rng.randint(2, self.width - 2), rng.randint(2, self.height - 2)
            self.tiles[y][x] = Tile.DIAMOND

        # Enemies — placed in open pockets so they have room to move
        types = ["diamond", "explosive"]
        for i in range(6):
            x = rng.randint(4, self.width  - 4)
            y = rng.randint(4, self.height - 4)
            self.enemy_spawns.append((x, y, types[i % 2]))

        # Exit — starts closed; game logic will open it when diamonds_required met
        self.tiles[self.height - 2][self.width - 2] = Tile.EXIT

        # Clear 3×3 spawn area so player isn't immediately blocked
        px, py = self.player_start
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                self.tiles[py + dy][px + dx] = Tile.EMPTY

import random
from tile import Tile
from constants import LEVEL_W, LEVEL_H

# Character encoding used in level files
CHAR_TO_TILE = {
    'W': Tile.WALL,
    ' ': Tile.EMPTY,
    '.': Tile.DIRT,
    'O': Tile.BOULDER,
    '*': Tile.DIAMOND,
    'X': Tile.EXIT,
    '~': Tile.SLIME,
}
_TILE_TO_CHAR  = {t: c for c, t in CHAR_TO_TILE.items()}
_ENEMY_TO_CHAR = {'diamond': 'd', 'explosive': 'e'}


class Level:
    def __init__(self):
        self.width             = LEVEL_W
        self.height            = LEVEL_H
        self.tiles             = [[Tile.EMPTY] * LEVEL_W for _ in range(LEVEL_H)]
        self.player_start      = (2, 2)
        self.diamonds_required = 10
        self.colour            = "blue"   # "blue", "red", or "green"
        self.enemy_spawns: list[tuple[int, int, str]] = []

    @classmethod
    def random(cls):
        level = cls()
        level._build_random()
        return level

    @classmethod
    def from_file(cls, path):
        level = cls()
        level._load_file(path)
        return level

    # ------------------------------------------------------------------
    # File I/O
    # ------------------------------------------------------------------

    def save_to_file(self, path):
        spawn_map = {(x, y): t for x, y, t in self.enemy_spawns}
        lines = [f"diamonds={self.diamonds_required}",
                 f"colour={self.colour}",
                 "---"]
        for y in range(self.height):
            row = []
            for x in range(self.width):
                if (x, y) == self.player_start:
                    row.append('P')
                elif (x, y) in spawn_map:
                    row.append(_ENEMY_TO_CHAR[spawn_map[(x, y)]])
                else:
                    row.append(_TILE_TO_CHAR.get(self.tiles[y][x], ' '))
            lines.append(''.join(row))
        with open(path, 'w') as f:
            f.write('\n'.join(lines) + '\n')

    def _load_file(self, path):
        with open(path) as f:
            text = f.read()

        if '---' in text:
            header, _, map_text = text.partition('---')
        else:
            header, map_text = '', text

        for line in header.splitlines():
            if '=' in line:
                key, _, val = line.partition('=')
                k, v = key.strip(), val.strip()
                if k == 'diamonds':
                    self.diamonds_required = int(v)
                elif k == 'colour' and v in ('blue', 'red', 'green'):
                    self.colour = v

        map_rows = [line for line in map_text.splitlines() if line]
        for y, row_str in enumerate(map_rows):
            if y >= self.height:
                break
            for x, ch in enumerate(row_str):
                if x >= self.width:
                    break
                if ch in CHAR_TO_TILE:
                    self.tiles[y][x] = CHAR_TO_TILE[ch]
                elif ch == 'P':
                    self.tiles[y][x] = Tile.EMPTY
                    self.player_start = (x, y)
                elif ch == 'd':
                    self.tiles[y][x] = Tile.EMPTY
                    self.enemy_spawns.append((x, y, 'diamond'))
                elif ch == 'e':
                    self.tiles[y][x] = Tile.EMPTY
                    self.enemy_spawns.append((x, y, 'explosive'))

    # ------------------------------------------------------------------
    # Random generation
    # ------------------------------------------------------------------

    # tiles[y][x] throughout
    def _build_random(self):
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

        for _ in range(1):
            x, y = rng.randint(4, self.width - 4), rng.randint(4, self.height - 4)
            self.tiles[y][x] = Tile.SLIME

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

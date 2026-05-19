import random
from tile import Tile
from tiles import Enemy1Tile, Enemy2Tile

# CCW rotation cycle (screen space): up → left → down → right → …
# Stepping +1 gives CCW; stepping -1 gives CW (up → right → down → left → …)
_DIRS = [(0, -1), (-1, 0), (0, 1), (1, 0)]  # up, left, down, right


class Enemy:
    tile_cls          = None
    diamond_explosion = False
    _rotation         = 1    # +1 CCW, -1 CW; set by subclass

    def __init__(self, x: int, y: int):
        self.x         = x
        self.y         = y
        self.alive     = True
        self.direction = random.choice(_DIRS)

    def sprite(self, frame: int):
        return self.tile_cls.sprite(frame)

    def update(self, tiles, occupied: set):
        idx = _DIRS.index(self.direction)
        for i in range(4):
            dx, dy = _DIRS[(idx + i * self._rotation) % 4]
            nx, ny = self.x + dx, self.y + dy
            if tiles[ny][nx] == Tile.EMPTY and (nx, ny) not in occupied:
                self.direction = (dx, dy)
                self.x = nx
                self.y = ny
                return
        # All directions blocked — stay still


class DiamondEnemy(Enemy):
    tile_cls  = Enemy1Tile
    _rotation = 1    # CCW: down → right → up → left


class ExplosiveEnemy(Enemy):
    tile_cls          = Enemy2Tile
    diamond_explosion = True   # leaves a 3×3 field of diamonds
    _rotation         = -1   # CW: down → left → up → right

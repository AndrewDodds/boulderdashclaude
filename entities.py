from tiles import Enemy1Tile, Enemy2Tile


class Enemy:
    tile_cls = None   # set by subclass

    def __init__(self, x: int, y: int):
        self.x     = x
        self.y     = y
        self.alive = True

    def sprite(self, frame: int):
        return self.tile_cls.sprite(frame)


class DiamondEnemy(Enemy):
    tile_cls         = Enemy1Tile
    diamond_explosion = False

class ExplosiveEnemy(Enemy):
    tile_cls         = Enemy2Tile
    diamond_explosion = True   # leaves a 3×3 field of diamonds

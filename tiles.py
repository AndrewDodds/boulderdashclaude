import pygame
from tile import Tile
from constants import TILE_SIZE

_sheet: pygame.Surface | None = None


def load_sheet(path: str) -> None:
    global _sheet
    _sheet = pygame.image.load(path).convert()


class TileBase:
    tile_type: Tile
    # Single-frame tiles set sheet_pos; animated tiles set sheet_frames instead.
    sheet_pos: tuple[int, int] = (0, 0)
    sheet_frames: list[tuple[int, int]] | None = None  # list of (col, row)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._cache: list[pygame.Surface] = []

    @classmethod
    def _load(cls) -> None:
        frames = cls.sheet_frames if cls.sheet_frames else [cls.sheet_pos]
        cls._cache = [
            _sheet.subsurface(
                pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            ).copy()
            for c, r in frames
        ]

    @classmethod
    def sprite(cls, frame: int = 0) -> pygame.Surface:
        if not cls._cache:
            cls._load()
        return cls._cache[frame % len(cls._cache)]

    @classmethod
    def frame_count(cls) -> int:
        return len(cls.sheet_frames) if cls.sheet_frames else 1


# ---------------------------------------------------------------------------
# Sprite positions reference bd_blue_big.png (320x256, 10x8 grid of 32x32).
# The same layout applies to bd_red_big.png and bd_green_big.png.
# ---------------------------------------------------------------------------

class EmptyTile(TileBase):
    tile_type   = Tile.EMPTY
    sheet_pos   = (6, 3)          # solid black square

class WallTile(TileBase):
    tile_type   = Tile.WALL
    sheet_pos   = (2, 3)          # crosshatch / brick pattern

class DirtTile(TileBase):
    tile_type    = Tile.DIRT
    sheet_frames = [(3, 3)]   # diagonal-stripe, 4 frames

class BoulderTile(TileBase):
    tile_type    = Tile.BOULDER
    sheet_frames = [(5, 3)]   #  rock, 1 frames

class DiamondTile(TileBase):
    tile_type    = Tile.DIAMOND
    sheet_frames = [(0, 4), (0, 5), (0, 6), (0, 7), (1, 4), (1, 5), (1, 6), (1, 7)]   # sparkling X, 4 frames

class ExitTile(TileBase):
    tile_type    = Tile.EXIT
    sheet_frames = [(0, 3)]   # pulsing square, 4 frames

class OpenExitTile(TileBase):
    tile_type    = Tile.EXIT
    sheet_frames = [(1, 3)]   # pulsing square, 4 frames

class PlayerTile(TileBase):
    sheet_frames = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0)]   # walk cycle, 7 frames

class ExplosionTile(TileBase):
    sheet_frames = [(7, 4), (8, 4), (7, 5), (8, 5)]   # 4-frame blast

class Enemy1Tile(TileBase):
    sheet_frames = [(5, 4), (5, 5), (5, 6), (5, 7)]

class Enemy2Tile(TileBase):
    sheet_frames = [(6, 4), (6, 5), (6, 6), (6, 7)]


TILE_CLASSES: dict[Tile, type[TileBase]] = {
    Tile.EMPTY:   EmptyTile,
    Tile.WALL:    WallTile,
    Tile.DIRT:    DirtTile,
    Tile.BOULDER: BoulderTile,
    Tile.DIAMOND: DiamondTile,
    Tile.EXIT:    ExitTile,
    Tile.OPENEXIT:    OpenExitTile,
}

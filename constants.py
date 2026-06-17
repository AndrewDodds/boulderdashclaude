import sys
import os


def resource_path(relative_path: str) -> str:
    """Resolve a path to a bundled resource (works both frozen and from source)."""
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)


TILE_SIZE = 32
COLS      = 20      # visible columns
ROWS      = 16      # visible rows
LEVEL_W   = 32      # full level width in tiles
LEVEL_H   = 32      # full level height in tiles
WIDTH     = COLS * TILE_SIZE   # 640
HEIGHT    = ROWS * TILE_SIZE   # 512

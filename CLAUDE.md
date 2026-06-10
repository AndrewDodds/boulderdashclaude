# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python implementation of the classic Pebbledash arcade game. The project is in its early stage — the spec and image assets exist but no source code has been written yet.

## Game Mechanics (from `Pebbledash.txt`)

- **World**: Grid of 32×32 tiles; 20×16 tiles visible at once, centered on the player
- **Border**: One-tile-thick impassable border surrounds the map
- **Tile types**: empty space, dirt, boulder, diamond, exit
- **Mobile entities**: diamond enemy, explosive enemy, player
- **Player movement**: arrow keys; moves freely through empty space
  - Moving into dirt: removes the dirt
  - Moving into a diamond: collects it (removed from map)
  - Cannot move into a boulder
- **Exit**: becomes available once enough diamonds are collected
- **Boulder physics**: falls if the tile below is empty
  - Hits player → player dies in a 3×3 explosion
  - Hits diamond enemy → enemy dies in a 3×3 explosion *of diamonds*
  - Hits explosive enemy → enemy dies in a 3×3 explosion
- **Explosion tile**: cycles through an animation then disappears
- **Caught in any explosion**: same result as being hit by a boulder

## Image Assets (`images/`)

The sprite sheets are classic Pebbledash tilesets; the `.xcf` files are the editable GIMP sources for the `.png` exports.

| File | Contents |
| --- | --- |
| `bd_blue.png` / `bd_blue_big.png` | Blue-palette Pebbledash sprite sheet (tiles, player frames, entities) |
| `bd_red_big.png` | Red-palette variant of the same sprite sheet |
| `bd_green_big.png` | Green-palette variant of the same sprite sheet |
| `Sci_Fi_C.png` | Sci-fi themed entity sprites (player character, enemies) |
| `Sci_Fi_A4.png` | Sci-fi wall/border tile blocks |
| `Sci_Fi_A5.png` | Color palette swatches for the sci-fi theme |
| `74444.png` | Duplicate of `bd_blue.png` |

## Python Environment

A `.venv` is present (Python 3.13). No game library has been added yet — pygame is the natural fit for a tile-based game loop with sprite rendering and keyboard input.

To activate the venv and install a library:
```bash
.venv\Scripts\activate
pip install pygame
```
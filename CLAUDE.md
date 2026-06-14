# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Tetris game implemented in Python using Pygame. Single-file architecture (`tetris.py`) with procedural sound generation (`generate_sounds.py`).

## Running the Game

```bash
python3 tetris.py
```

## Building macOS App

```bash
./build_app.sh          # builds with py2app and copies Tetris.app to ~/Desktop
```

Requires: `py2app`, `pygame`. The build script cleans `build/` and `dist/` before rebuilding.

## Regenerating Sounds

```bash
python3 generate_sounds.py   # writes .wav files into sounds/
```

Sound generation uses only the stdlib (`wave`, `struct`, `math`) — no audio libraries needed. Sounds are 22050Hz mono 16-bit WAVs using square/sine/sawtooth waves with AD envelopes.

## Architecture

**`tetris.py`** — the entire game in one file (~700 lines):

- **Constants** (lines 1-95): Grid dimensions, colors, SRS rotation tables (`SHAPES`, `WALL_KICKS`)
- **`Piece`** class: Holds type/position/rotation; `cells()` and `rotated_cells()` compute world coordinates from SHAPES table
- **`TetrisGame`** class: All game logic and rendering
  - Bag randomizer (`_fill_bag`/`_new_piece`) — 7-bag system
  - SRS rotation with wall kicks (`_try_rotate`)
  - DAS (Delayed Auto Shift) for held-left/right repeat (`das_delay=170ms`, `das_repeat=50ms`)
  - Lock delay (`lock_delay_max=500ms`) — resets when piece moves off ground
  - Ghost piece projection (`_ghost_y`)
  - Hold piece system (`_hold_piece`) — one hold per piece drop
  - T-Spin detection (`_is_t_spin`) — checks 3+ occupied corners of T-piece bounding box
  - Scoring: 100/300/500/800 × level for 1-4 lines; T-Spin single 400×level, double 800×level; soft drop +1/cell, hard drop +2/cell
  - Level progression: level = lines_cleared // 10 + 1; fall speed = max(50, 800 - (level-1)*70) ms
  - High score persisted to `~/.tetris_highscore.json`
  - Drawing: beveled 3D cells, ghost with alpha, sidebar with hold/next/stats/controls

**`generate_sounds.py`** — standalone script producing 9 sound effects in `sounds/`.

**`setup.py`** — py2app configuration for macOS app bundling; bundles `sounds/` as resources.

## Controls

← → Move | ↑ Rotate CW | Z Rotate CCW | ↓ Soft drop | Space Hard drop | C Hold | P Pause | R Restart (game over)

## Key Dependencies

- Python 3.9+
- Pygame (runtime)
- py2app (build only)

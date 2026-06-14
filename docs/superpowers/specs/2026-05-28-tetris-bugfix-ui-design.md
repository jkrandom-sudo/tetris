# Tetris Game Bug Fixes & UI Improvements Design

## Overview

Fix critical bugs, add GameState-based state management, implement title screen / pause / game over overlay menus with clickable buttons, and improve soft drop speed from 10x to 5x acceleration factor.

## Bug Fixes

### Critical

1. **Lock delay double counting** (lines 446-467): `lock_delay` increments by `speed` when gravity fails AND by `dt` in the lock delay section. Fix: remove the gravity-failure increment (`self.lock_delay += speed` at line 456); only accumulate `dt` in the "on ground" check.

2. **Sound plays before validation**: Move/rotate sounds play regardless of success. Fix: only play sounds when `_move()`, `_try_rotate()` return True. Hard drop sound: move after `_hard_drop()` call.

3. **Hold state not fully reset**: `reset()` doesn't reset `hold_used`, `das_direction`, `das_timer`, `das_charged`, `soft_dropping`, `t_spin_text`, `t_spin_display_timer`. Fix: add all to `reset()`.

4. **Soft drop sound every frame**: Plays on every update tick while soft dropping. Fix: add throttle — only play once per 100ms using a `_last_soft_drop_sound_time` tracker.

5. **Soft drop speed too slow**: Current `speed = max(30, speed // 10)` gives 10x acceleration. Change to `speed = max(30, speed // 5)` for 5x acceleration (more responsive).

6. **Sound ordering**: `level_up` sound check occurs after `game_over` is set, so it never plays on the final piece. Fix: check level_up before game_over.

### Medium (not in scope for this iteration)

- T-Spin detection completeness
- T-Spin scoring multipliers
- Wall kick index for counter-clockwise
- Ghost surface created per cell
- Score formatting with commas

These are documented but deferred to keep scope focused.

## State Management

Replace `game_over` + `paused` booleans with a `GameState` enum:

```python
class GameState:
    TITLE = "title"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"
```

Transition flow:
```
TITLE → PLAYING (click Start / press Enter)
PLAYING → PAUSED (click Pause / press P)
PAUSED → PLAYING (click Resume / press P)
PAUSED → TITLE (click Title / press Esc)
PAUSED → PLAYING (click Restart / press R — resets game)
GAME_OVER → PLAYING (click Restart / press R — resets game)
GAME_OVER → TITLE (click Title / press Esc)
```

`reset()` now sets state to PLAYING. A separate `go_to_title()` method sets state to TITLE and calls reset.

## UI Design

### Title Screen (GameState.TITLE)

- Dark background
- "TETRIS" title: large letters, each in a different piece color (I= cyan, O=yellow, T=purple, S=green, Z=red, J=blue, L=orange)
- "开始游戏" button: centered, rectangular, highlighted border, hover effect
- Controls info text below

### Sidebar Buttons (GameState.PLAYING)

- "⏸ 暂停" button at bottom of sidebar
- "↻ 重新开始" button below pause
- Both are clickable rectangles with hover highlight

### Pause Overlay (GameState.PAUSED)

- Semi-transparent dark overlay on board area
- "暂停" title text
- "继续游戏" button
- "重新开始" button
- "返回标题" button

### Game Over Overlay (GameState.GAME_OVER)

- Semi-transparent dark overlay on board area
- "游戏结束" title text
- Final score display
- "重新开始" button
- "返回标题" button

### Button System

A `Button` class with:
- `rect`: pygame.Rect for hit detection
- `text`: label string
- `callback`: function to call on click
- `hover`: bool for visual state
- `draw(surface)`: renders button with border + text
- `handle_event(event)`: checks mouse click/hover, calls callback

Mouse handling: on each frame, update hover state from `pygame.mouse.get_pos()`. On `MOUSEBUTTONDOWN`, check if click is inside any active button's rect.

## Implementation Scope

Single file `tetris.py` remains. Changes:

1. Add `GameState` enum and `Button` class at top of file
2. Add `self.state` to `TetrisGame.__init__`, set to `GameState.TITLE`
3. Modify `handle_events()` to route by state
4. Add `_draw_title_screen()`, `_draw_sidebar_buttons()`, `_draw_pause_overlay()`, `_draw_game_over_overlay()`
5. Modify `draw()` to dispatch by state
6. Modify `update()` to only run game logic in PLAYING state
7. Fix all bugs listed above
8. Update `reset()` to fully clear all state

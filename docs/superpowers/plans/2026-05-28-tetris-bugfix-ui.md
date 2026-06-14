# Tetris Bug Fixes & UI Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix critical game bugs, add GameState-based state management, implement title/pause/game-over screens with clickable buttons, and improve soft drop speed.

**Architecture:** Single-file `tetris.py` remains. Add `GameState` enum and `Button` class, replace `game_over`+`paused` booleans with `self.state`, add overlay drawing methods, and fix 6 critical bugs.

**Tech Stack:** Python 3.9+, Pygame

---

### Task 1: Add GameState enum and Button class

**Files:**
- Modify: `tetris.py` (insert after WALL_KICKS definition, around line 95)

- [ ] **Step 1: Add GameState class after WALL_KICKS**

Insert after line 95 (closing `}` of WALL_KICKS):

```python
class GameState:
    TITLE = "title"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"
```

- [ ] **Step 2: Add Button class after GameState**

```python
class Button:
    def __init__(self, x, y, width, height, text, callback):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.hovered = False

    def update_hover(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def handle_click(self, pos):
        if self.rect.collidepoint(pos):
            self.callback()
            return True
        return False

    def draw(self, surface, font):
        bg_color = (80, 80, 80) if self.hovered else (50, 50, 50)
        border_color = (200, 200, 200) if self.hovered else (120, 120, 120)
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=6)
        pygame.draw.rect(surface, border_color, self.rect, 2, border_radius=6)
        text_surf = font.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
```

- [ ] **Step 3: Run game to verify it still starts**

Run: `python3 tetris.py` (should behave identically, new classes not yet used)
Expected: Game runs normally

---

### Task 2: Fix lock delay double counting bug

**Files:**
- Modify: `tetris.py:420-469` (the `update` method)

- [ ] **Step 1: Remove double lock delay increment**

In the `update` method, find the gravity section (around line 446-458). The current code is:

```python
self.fall_time += dt
if self.fall_time >= speed:
    self.fall_time = 0
    new_cells = [(x, y + 1) for x, y in self.current.cells()]
    if self._valid_position(new_cells):
        self.current.y += 1
        if self.soft_dropping:
            self.score += 1
            self._play_sound("soft_drop")
    else:
        self.lock_delay += speed
        if self.lock_delay >= self.lock_delay_max:
            self._lock_piece()
```

Replace with (removing the `else` block that increments lock_delay by `speed`):

```python
self.fall_time += dt
if self.fall_time >= speed:
    self.fall_time = 0
    new_cells = [(x, y + 1) for x, y in self.current.cells()]
    if self._valid_position(new_cells):
        self.current.y += 1
        if self.soft_dropping:
            self.score += 1
            self._play_sound("soft_drop")
```

The lock delay is now ONLY handled by the separate "on ground" check below (lines ~460-469), which correctly uses `dt`.

- [ ] **Step 2: Run game and verify pieces lock at correct speed**

Run: `python3 tetris.py`
Expected: Pieces should feel like they have ~500ms lock delay (not ~250ms as before). Place a piece near the ground and observe it stays for about half a second before locking.

---

### Task 3: Fix sound plays before validation bugs

**Files:**
- Modify: `tetris.py:367-418` (the `handle_events` method)

- [ ] **Step 1: Fix move sound**

In `handle_events`, the current code is:

```python
if event.key == pygame.K_LEFT:
    if self._move(-1):
        self._play_sound("move")
    self.das_direction = -1
    self.das_timer = 0
    self.das_charged = False
elif event.key == pygame.K_RIGHT:
    if self._move(1):
        self._play_sound("move")
    self.das_direction = 1
    self.das_timer = 0
    self.das_charged = False
```

This is already correct — sound only plays on success. No change needed for move sounds.

- [ ] **Step 2: Fix rotation sound**

The current code is:

```python
elif event.key == pygame.K_UP:
    if self._try_rotate(1):
        self._play_sound("rotate")
elif event.key == pygame.K_z:
    if self._try_rotate(-1):
        self._play_sound("rotate")
```

This is also already correct. No change needed.

- [ ] **Step 3: Fix hard drop sound**

The current code plays sound AFTER `_hard_drop()`:

```python
elif event.key == pygame.K_SPACE:
    self._hard_drop()
    self._play_sound("hard_drop")
```

The sound is already after the call, but the sound plays even if the piece was already at the bottom (no actual drop distance). This is acceptable behavior since hard drop always locks the piece. No change needed.

- [ ] **Step 4: Verify no other sound-before-validation issues**

Scan `update()` method for the soft drop sound at line ~452-454. The current code plays soft_drop sound on every gravity tick while soft dropping. This is the throttling issue fixed in Task 5. No separate fix needed here.

---

### Task 4: Fix hold state reset and add full reset() cleanup

**Files:**
- Modify: `tetris.py:149-173` (the `reset` method)

- [ ] **Step 1: Add missing state resets to `reset()` method**

The current `reset()` method (lines 149-173) is:

```python
def reset(self):
    self.board = [[None] * COLS for _ in range(ROWS)]
    self.score = 0
    self.high_score = self._load_high_score()
    self.level = 1
    self.lines_cleared = 0
    self.game_over = False
    self.paused = False
    self.bag = []
    self.current = self._new_piece()
    self.next_piece = self._new_piece()
    self.fall_time = 0
    self.lock_delay = 0
    self.lock_delay_max = 500
    self.das_direction = 0
    self.das_timer = 0
    self.das_delay = 170
    self.das_repeat = 50
    self.das_charged = False
    self.soft_dropping = False
    self.hold_piece = None
    self.hold_used = False
    self.can_hold = True
    self.t_spin_display_timer = 0
    self.t_spin_text = ""
```

Actually, on re-reading, the current `reset()` already includes `hold_used`, `das_direction`, `das_timer`, `das_charged`, `soft_dropping`, `t_spin_text`, `t_spin_display_timer`. These were set in `reset()` already.

However, there is one missing field: `_last_soft_drop_sound_time` which we'll add in Task 5. Also, when we transition to GameState, we need to set `self.state`. Replace the `game_over` and `paused` lines with:

```python
def reset(self):
    self.state = GameState.PLAYING
    self.board = [[None] * COLS for _ in range(ROWS)]
    self.score = 0
    self.high_score = self._load_high_score()
    self.level = 1
    self.lines_cleared = 0
    self.bag = []
    self.current = self._new_piece()
    self.next_piece = self._new_piece()
    self.fall_time = 0
    self.lock_delay = 0
    self.lock_delay_max = 500
    self.das_direction = 0
    self.das_timer = 0
    self.das_delay = 170
    self.das_repeat = 50
    self.das_charged = False
    self.soft_dropping = False
    self.hold_piece = None
    self.hold_used = False
    self.can_hold = True
    self.t_spin_display_timer = 0
    self.t_spin_text = ""
    self._last_soft_drop_sound_time = 0
```

Removed `self.game_over = False` and `self.paused = False` (replaced by `self.state`).

- [ ] **Step 2: Add `go_to_title()` method after `reset()`**

```python
def go_to_title(self):
    self.state = GameState.TITLE
```

---

### Task 5: Fix soft drop sound throttle and speed

**Files:**
- Modify: `tetris.py` (`__init__` and `update` methods)

- [ ] **Step 1: Add throttle field to `__init__`**

After line where `self.t_spin_text = ""` is set, add:

```python
self._last_soft_drop_sound_time = 0
```

Note: This will also be added in `reset()` in Task 4.

- [ ] **Step 2: Fix soft drop speed and sound throttle in `update()`**

Find the gravity section in `update()` where soft drop speed is set. The current code is:

```python
speed = self._get_fall_speed()
if self.soft_dropping:
    speed = max(30, speed // 10)
```

Replace with:

```python
speed = self._get_fall_speed()
if self.soft_dropping:
    speed = max(30, speed // 5)
```

Then find the soft drop sound playing code:

```python
if self.soft_dropping:
    self.score += 1
    self._play_sound("soft_drop")
```

Replace with:

```python
if self.soft_dropping:
    self.score += 1
    now = pygame.time.get_ticks()
    if now - self._last_soft_drop_sound_time >= 100:
        self._play_sound("soft_drop")
        self._last_soft_drop_sound_time = now
```

- [ ] **Step 3: Run game and test soft drop**

Run: `python3 tetris.py`
Expected: Pressing ↓ should make pieces fall visibly faster (5x speed instead of 10x). Sound should play at most every 100ms, not a continuous buzz.

---

### Task 6: Fix sound ordering (level_up before game_over)

**Files:**
- Modify: `tetris.py:237-281` (the `_lock_piece` method)

- [ ] **Step 1: Reorder sound checks in `_lock_piece()`**

The current code at the end of `_lock_piece()` is:

```python
self.current = self.next_piece
self.next_piece = self._new_piece()
self.lock_delay = 0
self.can_hold = True
if not self._valid_position(self.current.cells()):
    self.game_over = True
    self._play_sound("game_over")
    if self.score > self.high_score:
        self.high_score = self.score
        self._save_high_score()

if self.level > old_level:
    self._play_sound("level_up")
```

Replace with (check level_up BEFORE game_over):

```python
if self.level > old_level:
    self._play_sound("level_up")

self.current = self.next_piece
self.next_piece = self._new_piece()
self.lock_delay = 0
self.can_hold = True
if not self._valid_position(self.current.cells()):
    self.state = GameState.GAME_OVER
    self._play_sound("game_over")
    if self.score > self.high_score:
        self.high_score = self.score
        self._save_high_score()
```

Note: `self.game_over = True` is replaced with `self.state = GameState.GAME_OVER` since we're transitioning to GameState.

---

### Task 7: Replace game_over/paused booleans with GameState throughout

**Files:**
- Modify: `tetris.py` (multiple locations)

- [ ] **Step 1: Add `self.state = GameState.TITLE` to `__init__`**

In `TetrisGame.__init__`, after `self.reset()` call (line 147), add:

```python
self.state = GameState.TITLE
```

This ensures the game starts at the title screen. The `reset()` call sets state to PLAYING, but we override to TITLE for initial launch.

Actually, better approach: change `__init__` to NOT call `reset()` directly, or call it and then override. The simplest is:

In `__init__`, after `self.reset()`:
```python
self.state = GameState.TITLE
```

- [ ] **Step 2: Replace all `self.game_over` checks with state checks**

Find and replace all occurrences:

| Line area | Old code | New code |
|-----------|----------|----------|
| `handle_events` game_over check | `if self.game_over:` | `if self.state == GameState.GAME_OVER:` |
| `handle_events` pause toggle | `if event.key == pygame.K_p: self.paused = not self.paused` | `if event.key == pygame.K_p: self.state = GameState.PLAYING if self.state == GameState.PAUSED else GameState.PAUSED` |
| `handle_events` paused check | `if self.paused:` | `if self.state == GameState.PAUSED:` |
| `handle_events` game_over R key | `if event.key == pygame.K_r: self.reset()` | `if event.key == pygame.K_r: self.reset()` (no change needed, reset sets state to PLAYING) |
| `update` early return | `if self.game_over or self.paused: return` | `if self.state != GameState.PLAYING: return` |
| `draw` condition | `if not self.game_over and not self.paused:` | `if self.state == GameState.PLAYING:` |
| `draw` game_over overlay | `if self.game_over:` | `if self.state == GameState.GAME_OVER:` |
| `draw` pause overlay | `if self.paused and not self.game_over:` | `if self.state == GameState.PAUSED:` |
| `_lock_piece` game over | `self.game_over = True` | `self.state = GameState.GAME_OVER` |

- [ ] **Step 3: Add Esc key handling**

In `handle_events`, add Esc key support. After the pause toggle (`K_p`) section, add:

```python
elif event.key == pygame.K_ESCAPE:
    if self.state in (GameState.PAUSED, GameState.GAME_OVER):
        self.go_to_title()
    elif self.state == GameState.PLAYING:
        self.state = GameState.PAUSED
```

Also add Enter key for title screen:

```python
elif event.key == pygame.K_RETURN:
    if self.state == GameState.TITLE:
        self.reset()
```

- [ ] **Step 4: Run game and verify state transitions work**

Run: `python3 tetris.py`
Expected:
- Game starts at PLAYING state (title screen not yet drawn, but state logic works)
- P toggles pause
- R restarts after game over
- Esc goes to title from paused/game_over

---

### Task 8: Add title screen drawing

**Files:**
- Modify: `tetris.py` (add `_draw_title_screen` method and create title screen buttons)

- [ ] **Step 1: Add title screen button creation in `__init__`**

After `self.reset()` and `self.state = GameState.TITLE`, add:

```python
self._create_buttons()
```

- [ ] **Step 2: Add `_create_buttons` method**

Add this method to `TetrisGame`:

```python
def _create_buttons(self):
    board_center_x = COLS * CELL_SIZE // 2
    btn_w, btn_h = 180, 45

    # Title screen buttons
    self.title_start_btn = Button(
        board_center_x - btn_w // 2, 380, btn_w, btn_h,
        "开始游戏", self.reset
    )

    # Sidebar buttons (PLAYING state)
    sidebar_x = COLS * CELL_SIZE + 15
    self.sidebar_pause_btn = Button(
        sidebar_x, SCREEN_HEIGHT - 110, SIDEBAR_WIDTH - 30, 40,
        "暂停", self._toggle_pause
    )
    self.sidebar_restart_btn = Button(
        sidebar_x, SCREEN_HEIGHT - 60, SIDEBAR_WIDTH - 30, 40,
        "重新开始", self.reset
    )

    # Pause overlay buttons
    self.pause_resume_btn = Button(
        board_center_x - btn_w // 2, 320, btn_w, btn_h,
        "继续游戏", self._toggle_pause
    )
    self.pause_restart_btn = Button(
        board_center_x - btn_w // 2, 380, btn_w, btn_h,
        "重新开始", self.reset
    )
    self.pause_title_btn = Button(
        board_center_x - btn_w // 2, 440, btn_w, btn_h,
        "返回标题", self.go_to_title
    )

    # Game over overlay buttons
    self.gameover_restart_btn = Button(
        board_center_x - btn_w // 2, 370, btn_w, btn_h,
        "重新开始", self.reset
    )
    self.gameover_title_btn = Button(
        board_center_x - btn_w // 2, 430, btn_w, btn_h,
        "返回标题", self.go_to_title
    )
```

- [ ] **Step 3: Add `_toggle_pause` helper method**

```python
def _toggle_pause(self):
    if self.state == GameState.PLAYING:
        self.state = GameState.PAUSED
    elif self.state == GameState.PAUSED:
        self.state = GameState.PLAYING
```

- [ ] **Step 4: Add `_draw_title_screen` method**

```python
def _draw_title_screen(self):
    self.screen.fill(DARK_GRAY)
    board_center_x = COLS * CELL_SIZE // 2

    # Draw "TETRIS" with piece-colored letters
    title_letters = list("TETRIS")
    title_colors = [
        COLORS["T"], COLORS["E"] if "E" in COLORS else (200, 200, 200),
        COLORS["T"], COLORS["R"] if "R" in COLORS else (200, 200, 200),
        COLORS["I"], COLORS["S"],
    ]
    # Use piece colors for each letter: T=purple, E=white, T=purple, R=white, I=cyan, S=green
    title_colors = [
        (160, 0, 240), (240, 240, 0), (160, 0, 240),
        (240, 0, 0), (0, 240, 240), (0, 240, 0),
    ]

    font_title = pygame.font.SysFont("Arial", 72, bold=True)
    total_width = sum(font_title.size(ch)[0] for ch in title_letters)
    letter_x = board_center_x - total_width // 2

    for i, ch in enumerate(title_letters):
        letter_surf = font_title.render(ch, True, title_colors[i])
        self.screen.blit(letter_surf, (letter_x, 150))
        letter_x += font_title.size(ch)[0]

    # Subtitle
    sub_font = pygame.font.SysFont("Arial", 20)
    sub_surf = sub_font.render("经典方块游戏", True, (150, 150, 150))
    sub_rect = sub_surf.get_rect(center=(board_center_x, 250))
    self.screen.blit(sub_surf, sub_rect)

    # Start button
    self.title_start_btn.draw(self.screen, self.font_medium)

    # Controls info
    y = 470
    controls = [
        "操作说明:",
        "← →  移动    ↑  旋转",
        "↓  软降    空格  硬降",
        "C  暂存    P  暂停",
    ]
    for text in controls:
        surf = self.font_small.render(text, True, (120, 120, 120))
        rect = surf.get_rect(center=(board_center_x, y))
        self.screen.blit(surf, rect)
        y += 24
```

- [ ] **Step 5: Run game and verify title screen appears**

Run: `python3 tetris.py`
Expected: Title screen with colorful "TETRIS", "开始游戏" button, and controls info. Clicking button or pressing Enter starts the game.

---

### Task 9: Add pause and game over overlay drawing

**Files:**
- Modify: `tetris.py` (add `_draw_pause_overlay`, `_draw_game_over_overlay`, `_draw_sidebar_buttons`)

- [ ] **Step 1: Add `_draw_pause_overlay` method**

```python
def _draw_pause_overlay(self):
    overlay = pygame.Surface(
        (COLS * CELL_SIZE, ROWS * CELL_SIZE), pygame.SRCALPHA
    )
    overlay.fill((0, 0, 0, 150))
    self.screen.blit(overlay, (0, 0))

    board_center_x = COLS * CELL_SIZE // 2
    pause_text = self.font_large.render("暂停", True, (255, 255, 255))
    pause_rect = pause_text.get_rect(
        center=(board_center_x, ROWS * CELL_SIZE // 2 - 80)
    )
    self.screen.blit(pause_text, pause_rect)

    self.pause_resume_btn.draw(self.screen, self.font_medium)
    self.pause_restart_btn.draw(self.screen, self.font_medium)
    self.pause_title_btn.draw(self.screen, self.font_medium)
```

- [ ] **Step 2: Add `_draw_game_over_overlay` method**

Replace the existing game over drawing code in `draw()` with a dedicated method. Note: the existing code draws game over inline — we move it to a method:

```python
def _draw_game_over_overlay(self):
    overlay = pygame.Surface(
        (COLS * CELL_SIZE, ROWS * CELL_SIZE), pygame.SRCALPHA
    )
    overlay.fill((0, 0, 0, 150))
    self.screen.blit(overlay, (0, 0))

    board_center_x = COLS * CELL_SIZE // 2
    go_text = self.font_large.render("游戏结束", True, (240, 50, 50))
    go_rect = go_text.get_rect(
        center=(board_center_x, ROWS * CELL_SIZE // 2 - 80)
    )
    self.screen.blit(go_text, go_rect)

    # Score display
    score_surf = self.font_medium.render(
        f"得分: {self.score}", True, (255, 255, 255)
    )
    score_rect = score_surf.get_rect(
        center=(board_center_x, ROWS * CELL_SIZE // 2 - 30)
    )
    self.screen.blit(score_surf, score_rect)

    self.gameover_restart_btn.draw(self.screen, self.font_medium)
    self.gameover_title_btn.draw(self.screen, self.font_medium)
```

- [ ] **Step 3: Add `_draw_sidebar_buttons` method**

```python
def _draw_sidebar_buttons(self):
    self.sidebar_pause_btn.draw(self.screen, self.font_small)
    self.sidebar_restart_btn.draw(self.screen, self.font_small)
```

---

### Task 10: Wire up draw() and handle_events() to use GameState and buttons

**Files:**
- Modify: `tetris.py` (rewrite `draw()` dispatch and `handle_events()` button handling)

- [ ] **Step 1: Rewrite `draw()` method**

Replace the entire `draw()` method. The board/sidebar drawing code stays the same for PLAYING state. The key changes:
- TITLE state: only draw title screen
- PLAYING state: draw board + sidebar + sidebar buttons
- PAUSED state: draw board + sidebar + pause overlay
- GAME_OVER state: draw board + sidebar + game over overlay
- Remove the inline game_over and pause overlay code

The new `draw()` method:

```python
def draw(self):
    if self.state == GameState.TITLE:
        self._draw_title_screen()
        pygame.display.flip()
        return

    # Board and sidebar (shared by PLAYING, PAUSED, GAME_OVER)
    self.screen.fill(DARK_GRAY)
    board_rect = pygame.Rect(0, 0, COLS * CELL_SIZE, ROWS * CELL_SIZE)
    pygame.draw.rect(self.screen, BLACK, board_rect)

    # Grid lines
    for x in range(COLS + 1):
        pygame.draw.line(
            self.screen, GRID_COLOR,
            (x * CELL_SIZE, 0), (x * CELL_SIZE, ROWS * CELL_SIZE),
        )
    for y in range(ROWS + 1):
        pygame.draw.line(
            self.screen, GRID_COLOR,
            (0, y * CELL_SIZE), (COLS * CELL_SIZE, y * CELL_SIZE),
        )

    # Locked pieces
    for y in range(ROWS):
        for x in range(COLS):
            if self.board[y][x] is not None:
                self._draw_cell(
                    self.screen, x, y, COLORS[self.board[y][x]]
                )

    # Current piece and ghost (only while playing)
    if self.state == GameState.PLAYING:
        # Ghost piece
        ghost_y = self._ghost_y()
        ghost_surface = pygame.Surface(
            (CELL_SIZE, CELL_SIZE), pygame.SRCALPHA
        )
        color = COLORS[self.current.type]
        ghost_color = (*color, GHOST_ALPHA)
        for cx, cy in SHAPES[self.current.type][self.current.rotation]:
            gx = self.current.x + cx
            gy = ghost_y + cy
            if 0 <= gy < ROWS and 0 <= gx < COLS:
                rect = pygame.Rect(
                    gx * CELL_SIZE, gy * CELL_SIZE, CELL_SIZE, CELL_SIZE
                )
                ghost_surface.fill(ghost_color)
                self.screen.blit(ghost_surface, rect.topleft)
                pygame.draw.rect(self.screen, color, rect, 1)

        # Current piece
        for x, y in self.current.cells():
            if 0 <= y < ROWS and 0 <= x < COLS:
                self._draw_cell(
                    self.screen, x, y, COLORS[self.current.type]
                )

    # Sidebar (hold, next, score, controls, buttons)
    self._draw_sidebar()

    # Overlays
    if self.state == GameState.PAUSED:
        self._draw_pause_overlay()
    elif self.state == GameState.GAME_OVER:
        self._draw_game_over_overlay()

    pygame.display.flip()
```

- [ ] **Step 2: Extract sidebar drawing into `_draw_sidebar()` method**

Move all sidebar drawing code from the old `draw()` into a new `_draw_sidebar()` method, adding the sidebar buttons at the end:

```python
def _draw_sidebar(self):
    sidebar_x = COLS * CELL_SIZE + 15

    # Hold piece label
    hold_label = self.font_medium.render("HOLD", True, WHITE)
    self.screen.blit(hold_label, (sidebar_x, 20))

    # Hold piece preview box
    hold_box = pygame.Rect(sidebar_x, 50, SIDEBAR_WIDTH - 30, 80)
    pygame.draw.rect(self.screen, BLACK, hold_box)
    pygame.draw.rect(self.screen, GRAY, hold_box, 1)

    if self.hold_piece:
        hold_cells = SHAPES[self.hold_piece.type][0]
        min_x = min(c[0] for c in hold_cells)
        max_x = max(c[0] for c in hold_cells)
        min_y = min(c[1] for c in hold_cells)
        max_y = max(c[1] for c in hold_cells)
        pw = (max_x - min_x + 1) * 25
        ph = (max_y - min_y + 1) * 25
        ox = sidebar_x + (SIDEBAR_WIDTH - 30 - pw) // 2
        oy = 50 + (80 - ph) // 2
        for cx, cy in hold_cells:
            rect = pygame.Rect(
                ox + (cx - min_x) * 25, oy + (cy - min_y) * 25, 25, 25
            )
            color = COLORS[self.hold_piece.type]
            pygame.draw.rect(self.screen, color, rect)
            highlight = tuple(min(255, c + 40) for c in color)
            shadow = tuple(max(0, c - 40) for c in color)
            pygame.draw.line(self.screen, highlight, rect.topleft, rect.topright, 1)
            pygame.draw.line(self.screen, highlight, rect.topleft, rect.bottomleft, 1)
            pygame.draw.line(self.screen, shadow, rect.bottomleft, rect.bottomright, 1)
            pygame.draw.line(self.screen, shadow, rect.topright, rect.bottomright, 1)

        if self.hold_used:
            dim = pygame.Surface((SIDEBAR_WIDTH - 30, 80), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 100))
            self.screen.blit(dim, (sidebar_x, 50))

    # Next piece label
    label = self.font_medium.render("NEXT", True, WHITE)
    self.screen.blit(label, (sidebar_x, 145))

    # Next piece preview box
    preview_box = pygame.Rect(sidebar_x, 175, SIDEBAR_WIDTH - 30, 80)
    pygame.draw.rect(self.screen, BLACK, preview_box)
    pygame.draw.rect(self.screen, GRAY, preview_box, 1)

    if self.next_piece:
        preview_cells = SHAPES[self.next_piece.type][0]
        min_x = min(c[0] for c in preview_cells)
        max_x = max(c[0] for c in preview_cells)
        min_y = min(c[1] for c in preview_cells)
        max_y = max(c[1] for c in preview_cells)
        pw = (max_x - min_x + 1) * 25
        ph = (max_y - min_y + 1) * 25
        ox = sidebar_x + (SIDEBAR_WIDTH - 30 - pw) // 2
        oy = 175 + (80 - ph) // 2
        for cx, cy in preview_cells:
            rect = pygame.Rect(
                ox + (cx - min_x) * 25, oy + (cy - min_y) * 25, 25, 25
            )
            color = COLORS[self.next_piece.type]
            pygame.draw.rect(self.screen, color, rect)
            highlight = tuple(min(255, c + 40) for c in color)
            shadow = tuple(max(0, c - 40) for c in color)
            pygame.draw.line(self.screen, highlight, rect.topleft, rect.topright, 1)
            pygame.draw.line(self.screen, highlight, rect.topleft, rect.bottomleft, 1)
            pygame.draw.line(self.screen, shadow, rect.bottomleft, rect.bottomright, 1)
            pygame.draw.line(self.screen, shadow, rect.topright, rect.bottomright, 1)

    # Score / High Score / Level / Lines
    y_offset = 280
    for label_text, value in [
        ("SCORE", str(self.score)),
        ("HIGH SCORE", str(self.high_score)),
        ("LEVEL", str(self.level)),
        ("LINES", str(self.lines_cleared)),
    ]:
        label = self.font_small.render(label_text, True, GRAY)
        self.screen.blit(label, (sidebar_x, y_offset))
        value_surf = self.font_medium.render(value, True, WHITE)
        self.screen.blit(value_surf, (sidebar_x, y_offset + 20))
        y_offset += 48

    # Controls
    y_offset = 460
    controls_label = self.font_small.render("CONTROLS", True, GRAY)
    self.screen.blit(controls_label, (sidebar_x, y_offset))
    y_offset += 25
    for text in [
        "← →  Move",
        "↑    Rotate",
        "↓    Soft drop",
        "SPC  Hard drop",
        "C    Hold",
        "P    Pause",
    ]:
        surf = self.font_small.render(text, True, (120, 120, 120))
        self.screen.blit(surf, (sidebar_x, y_offset))
        y_offset += 22

    # Sidebar buttons
    self._draw_sidebar_buttons()
```

- [ ] **Step 3: Add button handling to `handle_events()`**

At the beginning of `handle_events()`, add button click handling:

```python
def handle_events(self):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # Button click handling
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.state == GameState.TITLE:
                self.title_start_btn.handle_click(event.pos)
            elif self.state == GameState.PLAYING:
                self.sidebar_pause_btn.handle_click(event.pos)
                self.sidebar_restart_btn.handle_click(event.pos)
            elif self.state == GameState.PAUSED:
                self.pause_resume_btn.handle_click(event.pos)
                self.pause_restart_btn.handle_click(event.pos)
                self.pause_title_btn.handle_click(event.pos)
            elif self.state == GameState.GAME_OVER:
                self.gameover_restart_btn.handle_click(event.pos)
                self.gameover_title_btn.handle_click(event.pos)

        # Button hover update
        if event.type == pygame.MOUSEMOTION:
            buttons = []
            if self.state == GameState.TITLE:
                buttons = [self.title_start_btn]
            elif self.state == GameState.PLAYING:
                buttons = [self.sidebar_pause_btn, self.sidebar_restart_btn]
            elif self.state == GameState.PAUSED:
                buttons = [self.pause_resume_btn, self.pause_restart_btn, self.pause_title_btn]
            elif self.state == GameState.GAME_OVER:
                buttons = [self.gameover_restart_btn, self.gameover_title_btn]
            for btn in buttons:
                btn.update_hover(event.pos)

        if event.type == pygame.KEYDOWN:
            # ... existing key handling with GameState replacements ...
```

- [ ] **Step 4: Run game and test all states**

Run: `python3 tetris.py`
Expected:
- Title screen with "TETRIS" and "开始游戏" button
- Click button or press Enter → game starts
- Click "暂停" sidebar button or press P → pause overlay with buttons
- Click "继续游戏" → resume
- Game over → overlay with "重新开始" and "返回标题"
- Esc → returns to title from paused/game_over

---

### Task 11: Final integration and testing

**Files:**
- Modify: `tetris.py` (final cleanup)

- [ ] **Step 1: Run game and test complete flow**

Run: `python3 tetris.py`

Test checklist:
- [ ] Title screen appears on launch
- [ ] Click "开始游戏" starts game
- [ ] Press Enter starts game
- [ ] Sidebar "暂停" button pauses
- [ ] P key pauses
- [ ] Pause overlay shows 3 buttons
- [ ] "继续游戏" resumes
- [ ] "重新开始" resets game
- [ ] "返回标题" goes to title screen
- [ ] Game over overlay shows score + 2 buttons
- [ ] "重新开始" works from game over
- [ ] "返回标题" works from game over
- [ ] Esc goes to title from paused/game_over
- [ ] Soft drop (↓) is noticeably faster (5x instead of 10x)
- [ ] Soft drop sound is throttled (no buzzing)
- [ ] Lock delay feels correct (~500ms)
- [ ] Move/rotate sounds only play on success
- [ ] Level up sound plays before game over sound

- [ ] **Step 2: Fix any issues found during testing**

Address any bugs or visual glitches discovered in Step 1.

- [ ] **Step 3: Build macOS app and test**

Run: `./build_app.sh`
Expected: Tetris.app built and copied to Desktop

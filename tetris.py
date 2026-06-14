import pygame
import random
import sys
import os
import json

# --- Constants ---
CELL_SIZE = 30
COLS = 10
ROWS = 20
SIDEBAR_WIDTH = 200
SCREEN_WIDTH = COLS * CELL_SIZE + SIDEBAR_WIDTH
SCREEN_HEIGHT = ROWS * CELL_SIZE
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (50, 50, 50)
DARK_GRAY = (30, 30, 30)
GRID_COLOR = (40, 40, 40)
GHOST_ALPHA = 60

# Piece colors (vibrant palette)
COLORS = {
    "I": (0, 240, 240),
    "O": (240, 240, 0),
    "T": (160, 0, 240),
    "S": (0, 240, 0),
    "Z": (240, 0, 0),
    "J": (0, 0, 240),
    "L": (240, 160, 0),
}

# Tetromino shapes (relative positions for each rotation state)
SHAPES = {
    "I": [
        [(0, 1), (1, 1), (2, 1), (3, 1)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
        [(0, 2), (1, 2), (2, 2), (3, 2)],
        [(1, 0), (1, 1), (1, 2), (1, 3)],
    ],
    "O": [
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
    ],
    "T": [
        [(1, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (1, 2)],
        [(1, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "S": [
        [(1, 0), (2, 0), (0, 1), (1, 1)],
        [(1, 0), (1, 1), (2, 1), (2, 2)],
        [(1, 1), (2, 1), (0, 2), (1, 2)],
        [(0, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "Z": [
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(2, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (1, 2), (2, 2)],
        [(1, 0), (0, 1), (1, 1), (0, 2)],
    ],
    "J": [
        [(0, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 2)],
        [(1, 0), (1, 1), (0, 2), (1, 2)],
    ],
    "L": [
        [(2, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 2)],
        [(0, 1), (1, 1), (2, 1), (0, 2)],
        [(0, 0), (1, 0), (1, 1), (1, 2)],
    ],
}

# Wall kick data (SRS)
WALL_KICKS = {
    "default": [
        [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
        [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
        [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
        [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    ],
    "I": [
        [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],
        [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)],
        [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)],
        [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],
    ],
}


class GameState:
    TITLE = "title"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"


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


class Piece:
    def __init__(self, shape_type, x=3, y=0):
        self.type = shape_type
        self.x = x
        self.y = y
        self.rotation = 0

    def cells(self):
        return [
            (self.x + cx, self.y + cy)
            for cx, cy in SHAPES[self.type][self.rotation]
        ]

    def rotated_cells(self, direction=1):
        new_rot = (self.rotation + direction) % 4
        return [
            (self.x + cx, self.y + cy)
            for cx, cy in SHAPES[self.type][new_rot]
        ], new_rot


class TetrisGame:
    @staticmethod
    def _get_resource_path(relative_path):
        return os.path.join(
            os.path.dirname(os.path.abspath(__file__)), relative_path
        )

    def __init__(self):
        pygame.init()
        pygame.mixer.init(frequency=22050)
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Tetris")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.SysFont("stheitimedium", 36, bold=True)
        self.font_medium = pygame.font.SysFont("stheitimedium", 24)
        self.font_small = pygame.font.SysFont("stheitimedium", 18)

        # Load sounds
        self.sounds = {}
        sound_names = ["move", "rotate", "soft_drop", "hard_drop",
                       "line_clear", "tetris_clear", "game_over", "level_up", "hold"]
        for name in sound_names:
            path = self._get_resource_path(os.path.join("sounds", f"{name}.wav"))
            try:
                self.sounds[name] = pygame.mixer.Sound(path)
            except Exception:
                self.sounds[name] = None

        self.reset()
        self.state = GameState.TITLE
        self._create_buttons()

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

    def _toggle_pause(self):
        if self.state == GameState.PLAYING:
            self.state = GameState.PAUSED
        elif self.state == GameState.PAUSED:
            self.state = GameState.PLAYING

    def reset(self):
        self.board = [[None] * COLS for _ in range(ROWS)]
        self.score = 0
        self.high_score = self._load_high_score()
        self.level = 1
        self.lines_cleared = 0
        self.state = GameState.PLAYING
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

    def go_to_title(self):
        self.state = GameState.TITLE

    def _load_high_score(self):
        try:
            hs_path = os.path.expanduser("~/.tetris_highscore.json")
            with open(hs_path, "r") as f:
                data = json.load(f)
                return data.get("high_score", 0)
        except Exception:
            return 0

    def _save_high_score(self):
        try:
            hs_path = os.path.expanduser("~/.tetris_highscore.json")
            with open(hs_path, "w") as f:
                json.dump({"high_score": self.high_score}, f)
        except Exception:
            pass

    def _fill_bag(self):
        pieces = list("IOTSZJL")
        random.shuffle(pieces)
        self.bag = pieces

    def _new_piece(self):
        if not self.bag:
            self._fill_bag()
        shape_type = self.bag.pop()
        return Piece(shape_type)

    def _valid_position(self, cells):
        for x, y in cells:
            if x < 0 or x >= COLS or y >= ROWS:
                return False
            if y >= 0 and self.board[y][x] is not None:
                return False
        return True

    def _is_t_spin(self):
        """Check if the current piece is a T piece in a T-Spin configuration."""
        if self.current.type != "T":
            return False
        cells = self.current.cells()
        # Compute the 3x3 bounding box from actual cell positions
        min_x = min(c[0] for c in cells)
        max_x = max(c[0] for c in cells)
        min_y = min(c[1] for c in cells)
        max_y = max(c[1] for c in cells)
        # The bounding box is min_x..min_x+2 x min_y..min_y+2
        # (T piece always occupies 3 columns and 2-3 rows)
        corners = [
            (min_x, min_y),         # top-left
            (max_x, min_y),         # top-right
            (min_x, max_y),         # bottom-left
            (max_x, max_y),         # bottom-right
        ]
        occupied = 0
        for cx, cy in corners:
            if cx < 0 or cx >= COLS or cy >= ROWS:
                occupied += 1  # walls count as occupied
            elif cy >= 0 and self.board[cy][cx] is not None:
                occupied += 1
        return occupied >= 3

    def _lock_piece(self):
        # Check for T-Spin before locking
        t_spin = self._is_t_spin()
        lines_before = self.lines_cleared

        for x, y in self.current.cells():
            if 0 <= y < ROWS and 0 <= x < COLS:
                self.board[y][x] = self.current.type
        self._clear_lines()
        lines_this_clear = self.lines_cleared - lines_before

        # T-Spin bonus scoring and text display
        if t_spin and lines_this_clear > 0:
            if lines_this_clear == 1:
                self.score += 400 * self.level
                self.t_spin_text = "T-SPIN SINGLE!"
            elif lines_this_clear == 2:
                self.score += 800 * self.level
                self.t_spin_text = "T-SPIN DOUBLE!"
            self.t_spin_display_timer = 120  # ~2 seconds at 60fps

        # Play clear sounds
        if lines_this_clear == 4:
            self._play_sound("tetris_clear")
        elif lines_this_clear > 0:
            self._play_sound("line_clear")

        # Check level up
        old_level = self.level

        # Level up sound (check before game_over so it can play)
        if self.level > old_level:
            self._play_sound("level_up")

        self.current = self.next_piece
        self.next_piece = self._new_piece()
        self.lock_delay = 0
        self.can_hold = True  # Reset hold ability on new piece
        if not self._valid_position(self.current.cells()):
            self.state = GameState.GAME_OVER
            self._play_sound("game_over")
            # Save high score on game over
            if self.score > self.high_score:
                self.high_score = self.score
                self._save_high_score()

    def _clear_lines(self):
        lines = 0
        y = ROWS - 1
        while y >= 0:
            if all(self.board[y][x] is not None for x in range(COLS)):
                del self.board[y]
                self.board.insert(0, [None] * COLS)
                lines += 1
            else:
                y -= 1
        if lines > 0:
            points = {1: 100, 2: 300, 3: 500, 4: 800}
            self.score += points.get(lines, 0) * self.level
            self.lines_cleared += lines
            self.level = self.lines_cleared // 10 + 1

    def _ghost_y(self):
        ghost = Piece(self.current.type, self.current.x, self.current.y)
        ghost.rotation = self.current.rotation
        while self._valid_position(
            [(x, y + 1) for x, y in ghost.cells()]
        ):
            ghost.y += 1
        return ghost.y

    def _try_rotate(self, direction=1):
        new_cells, new_rot = self.current.rotated_cells(direction)
        kick_table = WALL_KICKS.get(
            "I" if self.current.type == "I" else "default"
        )
        kick_index = self.current.rotation if direction == 1 else new_rot
        for dx, dy in kick_table[kick_index]:
            kicked = [(x + dx, y + dy) for x, y in new_cells]
            if self._valid_position(kicked):
                self.current.x += dx
                self.current.y += dy
                self.current.rotation = new_rot
                return True
        return False

    def _move(self, dx):
        new_cells = [(x + dx, y) for x, y in self.current.cells()]
        if self._valid_position(new_cells):
            self.current.x += dx
            return True
        return False

    def _hard_drop(self):
        drop_dist = 0
        while self._valid_position(
            [(x, y + 1) for x, y in self.current.cells()]
        ):
            self.current.y += 1
            drop_dist += 1
        self.score += drop_dist * 2
        self._lock_piece()

    def _get_fall_speed(self):
        return max(50, 800 - (self.level - 1) * 70)

    def _hold_piece(self):
        if not self.can_hold or self.hold_used:
            return
        self.hold_used = True
        self._play_sound("hold")
        if self.hold_piece is None:
            self.hold_piece = Piece(self.current.type)
            self.current = self.next_piece
            self.next_piece = self._new_piece()
        else:
            current_type = self.current.type
            self.current = Piece(self.hold_piece.type)
            self.hold_piece = Piece(current_type)
        self.fall_time = 0
        self.lock_delay = 0

    def _play_sound(self, name):
        sound = self.sounds.get(name)
        if sound:
            try:
                sound.play()
            except Exception:
                pass

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
                if self.state == GameState.TITLE:
                    self.title_start_btn.update_hover(event.pos)
                elif self.state == GameState.PLAYING:
                    self.sidebar_pause_btn.update_hover(event.pos)
                    self.sidebar_restart_btn.update_hover(event.pos)
                elif self.state == GameState.PAUSED:
                    self.pause_resume_btn.update_hover(event.pos)
                    self.pause_restart_btn.update_hover(event.pos)
                    self.pause_title_btn.update_hover(event.pos)
                elif self.state == GameState.GAME_OVER:
                    self.gameover_restart_btn.update_hover(event.pos)
                    self.gameover_title_btn.update_hover(event.pos)

            if event.type == pygame.KEYDOWN:
                if self.state == GameState.TITLE:
                    if event.key == pygame.K_RETURN:
                        self.reset()
                    continue

                if self.state == GameState.GAME_OVER:
                    if event.key == pygame.K_r:
                        self.reset()
                    elif event.key == pygame.K_ESCAPE:
                        self.go_to_title()
                    continue

                if event.key == pygame.K_p:
                    self._toggle_pause()
                    continue

                if event.key == pygame.K_ESCAPE:
                    if self.state == GameState.PAUSED:
                        self.go_to_title()
                    elif self.state == GameState.PLAYING:
                        self.state = GameState.PAUSED
                    continue

                if self.state == GameState.PAUSED:
                    continue

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
                elif event.key == pygame.K_DOWN:
                    self.soft_dropping = True
                elif event.key == pygame.K_UP:
                    if self._try_rotate(1):
                        self._play_sound("rotate")
                elif event.key == pygame.K_z:
                    if self._try_rotate(-1):
                        self._play_sound("rotate")
                elif event.key == pygame.K_SPACE:
                    self._hard_drop()
                    self._play_sound("hard_drop")
                elif event.key == pygame.K_c:
                    self._hold_piece()

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT and self.das_direction == -1:
                    self.das_direction = 0
                elif event.key == pygame.K_RIGHT and self.das_direction == 1:
                    self.das_direction = 0
                elif event.key == pygame.K_DOWN:
                    self.soft_dropping = False

    def update(self, dt):
        if self.state != GameState.PLAYING:
            return

        # T-Spin display timer
        if self.t_spin_display_timer > 0:
            self.t_spin_display_timer -= 1

        # DAS (Delayed Auto Shift)
        if self.das_direction != 0:
            self.das_timer += dt
            if not self.das_charged:
                if self.das_timer >= self.das_delay:
                    self.das_charged = True
                    self.das_timer = 0
                    self._move(self.das_direction)
            else:
                if self.das_timer >= self.das_repeat:
                    self.das_timer = 0
                    self._move(self.das_direction)

        # Gravity
        speed = self._get_fall_speed()
        if self.soft_dropping:
            speed = 30

        self.fall_time += dt
        if self.fall_time >= speed:
            self.fall_time = 0
            new_cells = [(x, y + 1) for x, y in self.current.cells()]
            if self._valid_position(new_cells):
                self.current.y += 1
                if self.soft_dropping:
                    self.score += 1
                    now = pygame.time.get_ticks()
                    if now - self._last_soft_drop_sound_time >= 100:
                        self._play_sound("soft_drop")
                        self._last_soft_drop_sound_time = now

        # Lock delay
        on_ground = not self._valid_position(
            [(x, y + 1) for x, y in self.current.cells()]
        )
        if on_ground:
            self.lock_delay += dt
            if self.lock_delay >= self.lock_delay_max:
                self._lock_piece()
        else:
            self.lock_delay = 0

    def _draw_cell(self, surface, x, y, color, offset_x=0, offset_y=0, size=CELL_SIZE):
        rect = pygame.Rect(
            offset_x + x * size, offset_y + y * size, size, size
        )
        pygame.draw.rect(surface, color, rect)
        # Highlight (top-left bevel)
        highlight = tuple(min(255, c + 60) for c in color)
        shadow = tuple(max(0, c - 60) for c in color)
        pygame.draw.line(surface, highlight, rect.topleft, rect.topright, 2)
        pygame.draw.line(surface, highlight, rect.topleft, rect.bottomleft, 2)
        pygame.draw.line(surface, shadow, rect.bottomleft, rect.bottomright, 2)
        pygame.draw.line(surface, shadow, rect.topright, rect.bottomright, 2)

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

        # T-Spin display on board
        if self.t_spin_display_timer > 0:
            t_spin_surf = self.font_large.render(
                self.t_spin_text, True, (255, 255, 0)
            )
            t_spin_rect = t_spin_surf.get_rect(
                center=(COLS * CELL_SIZE // 2, ROWS * CELL_SIZE // 2)
            )
            self.screen.blit(t_spin_surf, t_spin_rect)

        # Sidebar
        self._draw_sidebar()

        # Overlays
        if self.state == GameState.PAUSED:
            self._draw_pause_overlay()
        elif self.state == GameState.GAME_OVER:
            self._draw_game_over_overlay()

        pygame.display.flip()

    def _draw_title_screen(self):
        self.screen.fill(DARK_GRAY)
        board_center_x = COLS * CELL_SIZE // 2

        # Draw "TETRIS" with piece-colored letters
        title_letters = list("TETRIS")
        title_colors = [
            (160, 0, 240), (240, 240, 0), (160, 0, 240),
            (240, 0, 0), (0, 240, 240), (0, 240, 0),
        ]

        font_title = pygame.font.SysFont("stheitimedium", 72, bold=True)
        total_width = sum(font_title.size(ch)[0] for ch in title_letters)
        letter_x = board_center_x - total_width // 2

        for i, ch in enumerate(title_letters):
            letter_surf = font_title.render(ch, True, title_colors[i])
            self.screen.blit(letter_surf, (letter_x, 150))
            letter_x += font_title.size(ch)[0]

        # Subtitle
        sub_surf = self.font_small.render("经典方块游戏", True, (150, 150, 150))
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
        self.sidebar_pause_btn.draw(self.screen, self.font_small)
        self.sidebar_restart_btn.draw(self.screen, self.font_small)

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

        score_surf = self.font_medium.render(
            f"得分: {self.score}", True, (255, 255, 255)
        )
        score_rect = score_surf.get_rect(
            center=(board_center_x, ROWS * CELL_SIZE // 2 - 30)
        )
        self.screen.blit(score_surf, score_rect)

        self.gameover_restart_btn.draw(self.screen, self.font_medium)
        self.gameover_title_btn.draw(self.screen, self.font_medium)

    def run(self):
        while True:
            dt = self.clock.tick(FPS)
            self.handle_events()
            self.update(dt)
            self.draw()


if __name__ == "__main__":
    game = TetrisGame()
    game.run()

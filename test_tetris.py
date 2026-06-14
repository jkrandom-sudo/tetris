#!/usr/bin/env python3
"""Tests for the pygame Tetris (`tetris.py`) core logic.

Runs headless via SDL_VIDEODRIVER=dummy. Covers init, movement,
rotation, line clearing, T-Spin detection, hold system (regression
guard for the once-per-game bug), level-up sound trigger, and
high-score persistence.
"""

import os
# Force headless BEFORE pygame import (tetris imports pygame at top-level)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import json
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tetris import (  # noqa: E402
    TetrisGame, Piece, GameState, COLS, ROWS, SHAPES, COLORS,
)


@pytest.fixture
def game():
    g = TetrisGame()
    # Force PLAYING state (reset already does this, but be explicit)
    g.state = GameState.PLAYING
    return g


# ---------- Init ----------

class TestInit:
    def test_board_dimensions(self, game):
        assert len(game.board) == ROWS
        assert all(len(row) == COLS for row in game.board)

    def test_board_empty_on_start(self, game):
        assert all(cell is None for row in game.board for cell in row)

    def test_score_starts_zero(self, game):
        assert game.score == 0

    def test_level_starts_one(self, game):
        assert game.level == 1

    def test_lines_starts_zero(self, game):
        assert game.lines_cleared == 0

    def test_current_and_next_present(self, game):
        assert game.current.type in SHAPES
        assert game.next_piece.type in SHAPES

    def test_hold_state_initial(self, game):
        assert game.hold_piece is None
        assert game.can_hold is True
        assert game.hold_used is False


# ---------- Movement & Rotation ----------

class TestMovement:
    def test_move_left(self, game):
        x_before = game.current.x
        moved = game._move(-1)
        if moved:
            assert game.current.x == x_before - 1

    def test_move_right(self, game):
        x_before = game.current.x
        moved = game._move(1)
        if moved:
            assert game.current.x == x_before + 1

    def test_move_left_wall_stops(self, game):
        # Move left aggressively
        for _ in range(20):
            game._move(-1)
        cells = game.current.cells()
        assert min(c[0] for c in cells) >= 0

    def test_move_right_wall_stops(self, game):
        for _ in range(20):
            game._move(1)
        cells = game.current.cells()
        assert max(c[0] for c in cells) < COLS

    def test_rotate_returns_bool(self, game):
        result = game._try_rotate(1)
        assert isinstance(result, bool)

    def test_rotate_keeps_piece_valid(self, game):
        game._try_rotate(1)
        assert game._valid_position(game.current.cells())


# ---------- Line clearing & scoring ----------

class TestLineClearing:
    def _fill_row(self, game, y, piece_type="I"):
        for x in range(COLS):
            game.board[y][x] = piece_type

    def test_single_clear_score(self, game):
        self._fill_row(game, ROWS - 1)
        game._clear_lines()
        assert game.lines_cleared == 1
        assert game.score == 100  # level 1

    def test_double_clear_score(self, game):
        self._fill_row(game, ROWS - 1)
        self._fill_row(game, ROWS - 2)
        game._clear_lines()
        assert game.lines_cleared == 2
        assert game.score == 300

    def test_triple_clear_score(self, game):
        for y in range(ROWS - 3, ROWS):
            self._fill_row(game, y)
        game._clear_lines()
        assert game.lines_cleared == 3
        assert game.score == 500

    def test_tetris_clear_score(self, game):
        for y in range(ROWS - 4, ROWS):
            self._fill_row(game, y)
        game._clear_lines()
        assert game.lines_cleared == 4
        assert game.score == 800

    def test_no_clear_on_partial_row(self, game):
        for x in range(COLS - 1):
            game.board[ROWS - 1][x] = "I"
        # leave one column empty
        game._clear_lines()
        assert game.lines_cleared == 0
        assert game.score == 0

    def test_level_up_after_10_lines(self, game):
        # Clear 10 lines one at a time
        for _ in range(10):
            self._fill_row(game, ROWS - 1)
            game._clear_lines()
        assert game.lines_cleared == 10
        assert game.level == 2

    def test_clear_shifts_rows_down(self, game):
        # Put a marker on row 0, fill bottom row, clear -> marker should
        # now be on row 1 (shifted down by 1).
        game.board[0][0] = "T"
        self._fill_row(game, ROWS - 1)
        game._clear_lines()
        assert game.board[0][0] is None
        assert game.board[1][0] == "T"


# ---------- 7-bag ----------

class TestBag:
    def test_bag_contains_all_pieces(self, game):
        game.bag = []
        game._fill_bag()
        assert sorted(game.bag) == sorted("IOTSZJL")

    def test_new_piece_refills_bag(self, game):
        game.bag = []
        p = game._new_piece()
        assert p.type in "IOTSZJL"
        assert len(game.bag) == 6


# ---------- Ghost ----------

class TestGhost:
    def test_ghost_at_or_below_current(self, game):
        gy = game._ghost_y()
        assert gy >= game.current.y

    def test_ghost_lands_on_floor_for_empty_board(self, game):
        gy = game._ghost_y()
        # The lowest cell of the piece at ghost position must equal ROWS-1
        # OR sit on something. For an empty board with default spawn, it
        # should land on the floor.
        cells_at_ghost = [
            (game.current.x + cx, gy + cy)
            for cx, cy in SHAPES[game.current.type][game.current.rotation]
        ]
        max_y = max(c[1] for c in cells_at_ghost)
        assert max_y == ROWS - 1


# ---------- Hold (regression: once-per-game bug) ----------

class TestHold:
    def test_first_hold_stores_piece(self, game):
        original_type = game.current.type
        game._hold_piece()
        assert game.hold_piece is not None
        assert game.hold_piece.type == original_type
        assert game.hold_used is True

    def test_cannot_hold_twice_for_same_piece(self, game):
        game._hold_piece()
        first_hold_type = game.hold_piece.type
        # second hold during the same drop must be a no-op
        game._hold_piece()
        assert game.hold_piece.type == first_hold_type

    def test_hold_resets_after_lock(self, game):
        """Regression: after a piece locks, the player must be able to hold again.

        Previously `hold_used` was never reset, breaking hold from the 2nd
        piece onward.
        """
        game._hold_piece()
        assert game.hold_used is True
        # simulate locking the current piece
        game._hard_drop()
        assert game.hold_used is False, (
            "hold_used must reset to False on new piece (was the bug)"
        )
        # And we should now be able to hold again
        game._hold_piece()
        assert game.hold_used is True


# ---------- T-Spin ----------

class TestTSpin:
    def test_non_t_piece_is_not_tspin(self, game):
        # Force current to non-T
        game.current = Piece("I", 3, 0)
        assert game._is_t_spin() is False

    def test_t_piece_in_open_field_is_not_tspin(self, game):
        game.current = Piece("T", 3, 5)
        # Empty board around it -> 0 corners occupied
        assert game._is_t_spin() is False

    def test_t_piece_with_3_corners_filled_is_tspin(self, game):
        # Place a T piece, fill 3 corners of its bounding box
        game.current = Piece("T", 3, 5)
        game.current.rotation = 0
        cells = game.current.cells()
        min_x = min(c[0] for c in cells)
        max_x = max(c[0] for c in cells)
        min_y = min(c[1] for c in cells)
        max_y = max(c[1] for c in cells)
        corners = [
            (min_x, min_y), (max_x, min_y),
            (min_x, max_y), (max_x, max_y),
        ]
        # Fill 3 of the 4 corners
        for cx, cy in corners[:3]:
            game.board[cy][cx] = "I"
        assert game._is_t_spin() is True


# ---------- Level-up sound trigger (regression) ----------

class TestLevelUpSound:
    def test_old_level_captured_before_clear(self, game, monkeypatch):
        """Regression: `old_level` must be captured BEFORE _clear_lines so
        the level_up sound actually fires."""
        played = []
        monkeypatch.setattr(game, "_play_sound", lambda name: played.append(name))

        # Pre-clear 9 lines so the next clear bumps us to level 2
        game.lines_cleared = 9
        game.level = 1
        # Fill bottom row, force current piece to a known location, then lock
        for x in range(COLS):
            game.board[ROWS - 1][x] = "I"
        # Spawn a harmless piece somewhere it can lock without blocking
        game.current = Piece("O", 4, 0)
        game._lock_piece()

        assert game.level == 2, "should have leveled up"
        assert "level_up" in played, (
            "level_up sound must fire on level transition"
        )


# ---------- High score persistence ----------

class TestHighScore:
    def test_save_and_load_roundtrip(self, game, tmp_path, monkeypatch):
        hs_file = tmp_path / "highscore.json"
        monkeypatch.setattr(
            os.path, "expanduser",
            lambda p: str(hs_file) if "tetris_highscore" in p else os.path.expanduser(p)
        )
        game.high_score = 12345
        game._save_high_score()
        assert hs_file.exists()
        data = json.loads(hs_file.read_text())
        assert data["high_score"] == 12345
        # Reload
        game.high_score = 0
        loaded = game._load_high_score()
        assert loaded == 12345


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

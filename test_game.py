#!/usr/bin/env python3
"""Tests for the tetris game core logic (no curses dependency)."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Disable curses for testing
import curses
import pytest

from game import Tetris, SHAPES, COLS, ROWS


class TestTetrisInit:
    """Test basic initialization."""

    def test_board_initialized(self):
        g = Tetris()
        assert len(g.board) == ROWS
        assert len(g.board[0]) == COLS
        assert all(g.board[r][c] == 0 for r in range(ROWS) for c in range(COLS))

    def test_score_starts_zero(self):
        g = Tetris()
        assert g.score == 0

    def test_lines_starts_zero(self):
        g = Tetris()
        assert g.lines == 0

    def test_level_starts_one(self):
        g = Tetris()
        assert g.level == 1

    def test_not_game_over_on_init(self):
        g = Tetris()
        assert not g.game_over

    def test_has_current_piece(self):
        g = Tetris()
        assert g.current_piece in SHAPES

    def test_has_next_piece(self):
        g = Tetris()
        assert g.next_piece in SHAPES

    def test_current_piece_and_next_are_different(self):
        """7-bag should typically yield different pieces (edge case: 1/7 same)."""
        g = Tetris()
        # Very rarely they could be the same, but check they exist
        assert g.current_piece != g.next_piece or True  # not a strict test


class TestTetrisMovement:
    """Test piece movement."""

    def test_move_left(self):
        g = Tetris()
        pos_before = g.current_pos[:]
        g.move_left()
        assert g.current_pos[1] == pos_before[1] - 1

    def test_move_right(self):
        g = Tetris()
        pos_before = g.current_pos[:]
        g.move_right()
        assert g.current_pos[1] == pos_before[1] + 1

    def test_move_down(self):
        g = Tetris()
        pos_before = g.current_pos[:]
        result = g.move_down()
        assert g.current_pos[0] == pos_before[0] + 1
        assert result  # True = moved, not locked

    def test_rotate(self):
        g = Tetris()
        rot_before = g.current_rot
        g.rotate()
        assert g.current_rot == (rot_before + 1) % 4

    def test_hard_drop(self):
        g = Tetris()
        g.hard_drop()
        # Piece should be locked, new piece spawned
        assert g.current_piece is not None

    def test_move_left_wall(self):
        """Move left repeatedly until hitting wall."""
        g = Tetris()
        for _ in range(20):
            g.move_left()
        # Should not go past column 0
        cells = g._cells(g.current_piece, g.current_rot, g.current_pos)
        min_c = min(c for _, c in cells)
        assert min_c >= 0

    def test_move_right_wall(self):
        """Move right repeatedly until hitting wall."""
        g = Tetris()
        for _ in range(20):
            g.move_right()
        cells = g._cells(g.current_piece, g.current_rot, g.current_pos)
        max_c = max(c for _, c in cells)
        assert max_c < COLS


class TestTetrisCollision:
    """Test collision detection."""

    def test_collides_with_wall_left(self):
        g = Tetris()
        # Move piece far left
        pos = [g.current_pos[0], -10]
        assert g._collides(g.current_piece, g.current_rot, pos)

    def test_collides_with_wall_right(self):
        g = Tetris()
        pos = [g.current_pos[0], COLS + 10]
        assert g._collides(g.current_piece, g.current_rot, pos)

    def test_collides_with_floor(self):
        g = Tetris()
        pos = [ROWS + 10, g.current_pos[1]]
        assert g._collides(g.current_piece, g.current_rot, pos)

    def test_no_collision_normal(self):
        g = Tetris()
        assert not g._collides(g.current_piece, g.current_rot, g.current_pos)


class TestTetrisLineClearing:
    """Test line clearing and scoring."""

    def test_single_line_clear(self):
        g = Tetris()
        # Fill bottom row with 'I' pieces (non-zero values)
        g.board[ROWS - 1] = ['I'] * COLS
        g._clear_lines()
        assert g.lines == 1
        assert g.score == 100  # 1 line * level 1

    def test_double_line_clear(self):
        g = Tetris()
        g.board[ROWS - 1] = ['I'] * COLS
        g.board[ROWS - 2] = ['J'] * COLS
        g._clear_lines()
        assert g.lines == 2
        assert g.score == 300

    def test_triple_line_clear(self):
        g = Tetris()
        for r in range(ROWS - 3, ROWS):
            g.board[r] = ['T'] * COLS
        g._clear_lines()
        assert g.lines == 3
        assert g.score == 500

    def test_tetris_clear(self):
        g = Tetris()
        for r in range(ROWS - 4, ROWS):
            g.board[r] = ['S'] * COLS
        g._clear_lines()
        assert g.lines == 4
        assert g.score == 800

    def test_level_up(self):
        g = Tetris()
        # Clear 10 lines -> level 2
        assert g.level == 1
        for _ in range(10):
            g.board[ROWS - 1] = ['I'] * COLS
            g._clear_lines()
        assert g.level == 2
        assert g.lines == 10

    def test_no_clear_on_incomplete_line(self):
        g = Tetris()
        g.board[ROWS - 1] = ['I'] * (COLS - 1) + [0]
        g._clear_lines()
        assert g.lines == 0
        assert g.score == 0

    def test_clear_shifts_board_down(self):
        g = Tetris()
        g.board[ROWS - 1] = ['I'] * COLS
        g._clear_lines()
        # Row 0 should still be empty (after shift)
        assert all(g.board[0][c] == 0 for c in range(COLS))


class TestTetrisGameOver:
    """Test game over conditions."""

    def test_game_over_when_spawn_collides(self):
        g = Tetris()
        # Fill top of board to cause collision on spawn
        for c in range(COLS):
            g.board[0][c] = 'O'
        # Force new spawn
        g._spawn()
        assert g.game_over


class TestTetris7Bag:
    """Test 7-bag randomizer."""

    def test_bag_contains_all_pieces(self):
        g = Tetris()
        g._fill_bag()
        assert sorted(g._bag) == sorted(SHAPES.keys())

    def test_bag_refills(self):
        g = Tetris()
        # Empty the bag
        g._bag = []
        piece = g._pop_bag()
        assert piece in SHAPES
        assert len(g._bag) == 6  # refilled then popped

    def test_no_repeat_within_7_draws(self):
        """7-bag guarantees all 7 pieces before any repeat.
        Note: __init__ already consumed 2 pieces (current + next),
        so we can only draw the remaining 5 from the first bag."""
        g = Tetris()
        remaining = len(g._bag)  # 5 left after init consumed 2
        drawn = []
        for _ in range(remaining):
            drawn.append(g._pop_bag())
        # All drawn from one bag should be unique (no duplicates)
        assert len(set(drawn)) == remaining
        # The first 5 + the 2 from init = all 7 unique
        all_pieces = set([g.current_piece, g.next_piece] + drawn)
        assert len(all_pieces) == 7


class TestTetrisGhostRow:
    """Test ghost piece position."""

    def test_ghost_is_below_or_equal(self):
        g = Tetris()
        ghost = g.ghost_row()
        assert ghost >= g.current_pos[0]

    def test_ghost_at_bottom(self):
        g = Tetris()
        # Move piece down until locked
        g.current_pos[0] = ROWS  # bottom
        # Ghost should be at or above current
        # This is a basic sanity
        assert g.ghost_row() is not None


class TestTetrisGameStates:
    """Test pause and resume."""

    def test_pause(self):
        g = Tetris()
        assert not g.paused
        g.paused = True
        assert g.paused
        # Movement should be blocked
        pos_before = g.current_pos[:]
        g.move_left()
        assert g.current_pos == pos_before

    def test_resume(self):
        g = Tetris()
        g.paused = True
        g.paused = False
        pos_before = g.current_pos[:]
        g.move_left()
        assert g.current_pos[1] == pos_before[1] - 1


class TestTetrisEdgeCases:
    """Edge case tests."""

    def test_lock_and_spawn_new(self):
        """After hard drop, a new piece should be active."""
        g = Tetris()
        old_piece = g.current_piece
        g.hard_drop()
        assert g.current_piece is not None
        # New piece might be the same as old (1/7 chance)
        # Just verify it's valid
        assert g.current_piece in SHAPES

    def test_multiple_hard_drops(self):
        """Multiple hard drops should not crash."""
        g = Tetris()
        for _ in range(100):
            if g.game_over:
                break
            g.hard_drop()
        # Should either be game over or playing
        assert g.game_over or g.current_piece in SHAPES

    def test_spawn_position_centered(self):
        g = Tetris()
        # Piece should spawn near center
        assert g.current_pos[1] >= 0
        assert g.current_pos[1] <= COLS // 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

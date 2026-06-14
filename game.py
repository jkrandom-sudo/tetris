#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
俄罗斯方块 - Console Tetris Game
运行方式: python3 game.py
"""

import curses
import random
import sys

# === 常量 ===
COLS = 10
ROWS = 20

# 七种方块（每种 4 个旋转状态，每个状态是相对于原点的 (row, col) 偏移列表）
SHAPES = {
    'I': [
        [(0, 0), (0, 1), (0, 2), (0, 3)],
        [(0, 0), (1, 0), (2, 0), (3, 0)],
        [(0, 0), (0, 1), (0, 2), (0, 3)],
        [(0, 0), (1, 0), (2, 0), (3, 0)],
    ],
    'O': [
        [(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 0), (1, 1)],
    ],
    'T': [
        [(0, 1), (1, 0), (1, 1), (1, 2)],
        [(0, 0), (1, 0), (1, 1), (2, 0)],
        [(0, 0), (0, 1), (0, 2), (1, 1)],
        [(0, 1), (1, 0), (1, 1), (2, 1)],
    ],
    'S': [
        [(0, 1), (0, 2), (1, 0), (1, 1)],
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(0, 1), (0, 2), (1, 0), (1, 1)],
        [(0, 0), (1, 0), (1, 1), (2, 1)],
    ],
    'Z': [
        [(0, 0), (0, 1), (1, 1), (1, 2)],
        [(0, 1), (1, 0), (1, 1), (2, 0)],
        [(0, 0), (0, 1), (1, 1), (1, 2)],
        [(0, 1), (1, 0), (1, 1), (2, 0)],
    ],
    'J': [
        [(0, 0), (1, 0), (1, 1), (1, 2)],
        [(0, 0), (0, 1), (1, 0), (2, 0)],
        [(0, 0), (0, 1), (0, 2), (1, 2)],
        [(0, 1), (1, 1), (2, 0), (2, 1)],
    ],
    'L': [
        [(0, 2), (1, 0), (1, 1), (1, 2)],
        [(0, 0), (1, 0), (2, 0), (2, 1)],
        [(0, 0), (0, 1), (0, 2), (1, 0)],
        [(0, 0), (0, 1), (1, 1), (2, 1)],
    ],
}

# 方块颜色映射（curses 颜色对编号）
COLOR_MAP = {
    'I': 1,  # 青色
    'O': 2,  # 黄色
    'T': 3,  # 紫色
    'S': 4,  # 绿色
    'Z': 5,  # 红色
    'J': 6,  # 蓝色
    'L': 7,  # 白色
}


class Tetris:
    """俄罗斯方块游戏核心逻辑"""

    def __init__(self):
        self.board = [[0] * COLS for _ in range(ROWS)]
        self.score = 0
        self.lines = 0
        self.level = 1
        self.game_over = False
        self.paused = False

        self.current_piece = None   # 当前方块类型名
        self.current_pos = None     # [row, col] 左上角位置
        self.current_rot = 0        # 当前旋转索引 (0-3)
        self.next_piece = None      # 下一个方块

        self._bag = []              # 7-bag 随机池
        self._fill_bag()
        self._spawn()

    # ---- 7-bag 随机算法 ----

    def _fill_bag(self):
        self._bag = list(SHAPES.keys())
        random.shuffle(self._bag)

    def _pop_bag(self):
        if not self._bag:
            self._fill_bag()
        return self._bag.pop()

    # ---- 生成 / 锁定 ----

    def _spawn(self):
        if self.next_piece is None:
            self.next_piece = self._pop_bag()
        self.current_piece = self.next_piece
        self.next_piece = self._pop_bag()
        self.current_rot = 0
        self.current_pos = [0, COLS // 2 - 2]
        if self._collides(self.current_piece, self.current_rot, self.current_pos):
            self.game_over = True

    def _lock(self):
        for r, c in self._cells(self.current_piece, self.current_rot, self.current_pos):
            if 0 <= r < ROWS and 0 <= c < COLS:
                self.board[r][c] = self.current_piece
        self._clear_lines()
        self._spawn()

    # ---- 碰撞检测 ----

    def _cells(self, piece, rot, pos):
        """返回方块所有格子绝对坐标 [(r,c), ...]"""
        return [(pos[0] + dr, pos[1] + dc) for dr, dc in SHAPES[piece][rot]]

    def _collides(self, piece, rot, pos):
        for r, c in self._cells(piece, rot, pos):
            if r < 0 or r >= ROWS or c < 0 or c >= COLS:
                return True
            if self.board[r][c]:
                return True
        return False

    # ---- 消行 ----

    def _clear_lines(self):
        cleared = 0
        r = ROWS - 1
        while r >= 0:
            if all(self.board[r]):
                del self.board[r]
                self.board.insert(0, [0] * COLS)
                cleared += 1
                # Don't decrement r — after deletion + insert, the next row
                # to check shifted into the same index
            else:
                r -= 1
        if cleared:
            self.lines += cleared
            points = [0, 100, 300, 500, 800]
            self.score += points[min(cleared, 4)] * self.level
            self.level = self.lines // 10 + 1

    # ---- 玩家操作 ----

    def move_left(self):
        if self.game_over or self.paused:
            return
        p = [self.current_pos[0], self.current_pos[1] - 1]
        if not self._collides(self.current_piece, self.current_rot, p):
            self.current_pos = p

    def move_right(self):
        if self.game_over or self.paused:
            return
        p = [self.current_pos[0], self.current_pos[1] + 1]
        if not self._collides(self.current_piece, self.current_rot, p):
            self.current_pos = p

    def move_down(self):
        if self.game_over or self.paused:
            return False
        p = [self.current_pos[0] + 1, self.current_pos[1]]
        if not self._collides(self.current_piece, self.current_rot, p):
            self.current_pos = p
            return True
        self._lock()
        return False

    def rotate(self):
        if self.game_over or self.paused:
            return
        nr = (self.current_rot + 1) % 4
        if not self._collides(self.current_piece, nr, self.current_pos):
            self.current_rot = nr

    def hard_drop(self):
        if self.game_over or self.paused:
            return
        while True:
            p = [self.current_pos[0] + 1, self.current_pos[1]]
            if not self._collides(self.current_piece, self.current_rot, p):
                self.current_pos = p
            else:
                break
        self._lock()

    def ghost_row(self):
        """返回幽灵方块（落点预览）的行偏移"""
        row = self.current_pos[0]
        while not self._collides(self.current_piece, self.current_rot,
                                 [row + 1, self.current_pos[1]]):
            row += 1
        return row


# === 渲染 ===

def draw(stdscr, game):
    h, w = stdscr.getmaxyx()
    stdscr.clear()

    # 标题
    title = "俄罗斯方块"
    stdscr.addstr(0, w // 2 - len(title) // 2, title, curses.A_BOLD)

    # 棋盘区域左上角
    bx = w // 2 - COLS - 5
    by = 2

    # 边框
    for r in range(ROWS + 1):
        stdscr.addstr(by + r, bx, "│")
        stdscr.addstr(by + r, bx + COLS * 2 + 1, "│")
    stdscr.addstr(by - 1, bx, "┌" + "─" * (COLS * 2 + 1) + "┐")
    stdscr.addstr(by + ROWS + 1, bx, "└" + "─" * (COLS * 2 + 1) + "┘")

    # 已固定的方块
    for r in range(ROWS):
        for c in range(COLS):
            x = bx + 1 + c * 2
            y = by + r
            if game.board[r][c]:
                cp = COLOR_MAP.get(game.board[r][c], 0)
                stdscr.addstr(y, x, "■", curses.color_pair(cp))
            else:
                stdscr.addstr(y, x, "·")

    if game.current_piece and not game.game_over:
        # 幽灵方块
        ghost_r = game.ghost_row()
        for r, c in game._cells(game.current_piece, game.current_rot,
                                [ghost_r, game.current_pos[1]]):
            if 0 <= r < ROWS and 0 <= c < COLS:
                stdscr.addstr(by + r, bx + 1 + c * 2, "□", curses.A_DIM)

        # 当前方块
        cp = COLOR_MAP.get(game.current_piece, 0)
        for r, c in game._cells(game.current_piece, game.current_rot, game.current_pos):
            if 0 <= r < ROWS and 0 <= c < COLS:
                stdscr.addstr(by + r, bx + 1 + c * 2, "■", curses.color_pair(cp))

    # 信息面板
    ix = bx + COLS * 2 + 5
    iy = by
    stdscr.addstr(iy, ix, "得分", curses.A_BOLD)
    iy += 1
    stdscr.addstr(iy, ix, str(game.score))
    iy += 2
    stdscr.addstr(iy, ix, "行数", curses.A_BOLD)
    iy += 1
    stdscr.addstr(iy, ix, str(game.lines))
    iy += 2
    stdscr.addstr(iy, ix, "等级", curses.A_BOLD)
    iy += 1
    stdscr.addstr(iy, ix, str(game.level))
    iy += 2

    # 下一个方块预览
    stdscr.addstr(iy, ix, "下一个", curses.A_BOLD)
    iy += 1
    if game.next_piece:
        cp = COLOR_MAP.get(game.next_piece, 0)
        for r, c in SHAPES[game.next_piece][0]:
            stdscr.addstr(iy + r, ix + c * 2, "■", curses.color_pair(cp))

    iy += 5
    stdscr.addstr(iy, ix, "操作", curses.A_BOLD)
    iy += 1
    stdscr.addstr(iy, ix, "← →  移动")
    iy += 1
    stdscr.addstr(iy, ix, "↑    旋转")
    iy += 1
    stdscr.addstr(iy, ix, "↓    加速")
    iy += 1
    stdscr.addstr(iy, ix, "空格  落底")
    iy += 1
    stdscr.addstr(iy, ix, "p    暂停")
    iy += 1
    stdscr.addstr(iy, ix, "q    退出")

    # 游戏结束 / 暂停
    if game.game_over:
        msg = "游戏结束!"
        stdscr.addstr(by + ROWS // 2, bx + COLS - 3, msg,
                      curses.A_BOLD | curses.A_BLINK)
        stdscr.addstr(by + ROWS // 2 + 1, bx + COLS - 6, "按 r 重新开始",
                      curses.A_BOLD)

    if game.paused:
        stdscr.addstr(by + ROWS // 2, bx + COLS - 2, "暂停中", curses.A_BOLD)

    stdscr.refresh()


# === 主循环 ===

def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(80)

    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(6, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLACK)

    game = Tetris()
    tick = 0

    while True:
        key = stdscr.getch()

        if key == ord('q'):
            break
        if key == ord('r') and game.game_over:
            game = Tetris()
            tick = 0
            continue
        if key == ord('p'):
            game.paused = not game.paused
            continue

        if game.game_over or game.paused:
            draw(stdscr, game)
            continue

        # 按键处理
        if key == curses.KEY_LEFT:
            game.move_left()
        elif key == curses.KEY_RIGHT:
            game.move_right()
        elif key == curses.KEY_DOWN:
            game.move_down()
        elif key == curses.KEY_UP:
            game.rotate()
        elif key == ord(' '):
            game.hard_drop()

        # 自动下落（等级越高越快）
        interval = max(3, 11 - game.level)
        tick += 1
        if tick >= interval:
            tick = 0
            game.move_down()

        draw(stdscr, game)


if __name__ == '__main__':
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        sys.exit(0)

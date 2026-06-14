# Tetris 俄罗斯方块

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Pygame](https://img.shields.io/badge/Pygame-2.5%2B-green.svg)](https://www.pygame.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](#许可证)

经典俄罗斯方块的 Python 实现，提供 **图形界面** 和 **终端命令行** 两种版本，特性全面对齐现代 Tetris Guideline（SRS 旋转、7-bag、Hold、T-Spin 等），支持打包为 macOS 应用。

---

## ✨ 功能特性

### 通用游戏机制
- 🎯 **7-bag 随机器** — 每 7 块保证 7 种方块各出现一次，避免长期"饥饿"
- 🔄 **SRS 旋转系统** — 标准 Super Rotation System，含 I 型独立 wall kick 表
- 👻 **Ghost 投影** — 半透明显示方块落点
- 📦 **Hold 暂存系统** — 每块限用一次，按 `C` 切换
- ⏱ **Lock Delay** — 触底后 500ms 缓冲，期间移动会重置计时
- 🎮 **DAS 自动平移** — 长按方向键时延迟 170ms 后以 50ms 间隔自动重复
- ✨ **T-Spin 检测与加分** — 三角占用法判定 T-Spin Single / Double
- 📈 **关卡系统** — 每消 10 行升 1 级，下落速度从 800ms → 50ms 渐进加速

### 计分规则

| 操作 | 得分 |
|------|------|
| 单消 (Single) | 100 × level |
| 双消 (Double) | 300 × level |
| 三消 (Triple) | 500 × level |
| 四消 (Tetris) | 800 × level |
| T-Spin Single | 400 × level |
| T-Spin Double | 800 × level |
| Soft Drop | +1 / 格 |
| Hard Drop | +2 / 格 |

### 图形版独有
- 🎨 **3D 立体方块** — 高光 / 阴影边缘
- 🔊 **9 种音效** — 程序化生成，无需额外音频库
- 💾 **最高分持久化** — 保存于 `~/.tetris_highscore.json`
- 🖱 **完整 UI** — 标题屏 / 暂停遮罩 / 游戏结束遮罩 / 侧边栏（Hold + Next + Stats）
- 🖼 **可打包为 macOS 应用**（py2app）

---

## 📦 安装

### 依赖
- Python **3.9+**
- 图形版：`pygame >= 2.5`
- 终端版：仅 stdlib（curses，macOS / Linux 自带；Windows 需 `windows-curses`）

### 快速开始

```bash
# 克隆仓库
git clone https://github.com/jkrandom-sudo/tetris.git
cd tetris

# 安装 pygame（仅图形版需要）
pip install pygame
```

---

## 🎮 运行

### 图形界面版（推荐）

```bash
python3 tetris.py
```

完整特性版本，含音效、Hold、T-Spin、最高分等。

### 终端命令行版

```bash
python3 game.py
```

无依赖、即开即玩的 curses 版本，适合 SSH 远程 / 无图形环境。

### macOS 应用打包

```bash
./build_app.sh
```

会用 py2app 构建 `Tetris.app` 并复制到 `~/Desktop`。需要先 `pip install py2app`。

### 重新生成音效

```bash
python3 generate_sounds.py
```

仅用 stdlib（`wave` / `struct` / `math`）生成 9 个 22050Hz 单声道 16bit WAV，使用方波 / 正弦 / 锯齿波 + AD 包络。

---

## ⌨️ 操作

| 按键 | 功能 |
|------|------|
| ← → | 左右移动 |
| ↑ | 顺时针旋转 |
| `Z` | 逆时针旋转（仅图形版） |
| ↓ | 软降 |
| `Space` | 硬降 |
| `C` | Hold 暂存 / 取出（仅图形版） |
| `P` | 暂停 / 继续 |
| `Esc` | 暂停时返回标题（仅图形版） |
| `R` | 游戏结束后重新开始 |

---

## 🧪 测试

```bash
pip install pytest
pytest -v                      # 运行全部测试（推荐）
pytest test_game.py -v         # 仅终端版
pytest test_tetris.py -v       # 仅图形版（headless，自动设置 SDL dummy）
```

- `test_game.py` — 覆盖终端版（`game.py`）：初始化 / 移动 / 碰撞 / 消行计分 / 升级 / 7-bag / Ghost / 暂停 / 边界。
- `test_tetris.py` — 覆盖图形版（`tetris.py`）：初始化 / 移动 / 旋转 / 消行计分 / 升级 / 7-bag / Ghost / **Hold（含一次性 bug 回归测试）** / **T-Spin 检测** / **Level-up 音效触发回归** / 高分持久化。

---

## 📁 项目结构

```
tetris-game/
├── tetris.py              # 图形版（Pygame，~900 行单文件实现）
├── game.py                # 终端版（curses）
├── test_game.py           # 针对 game.py 的 pytest 测试
├── test_tetris.py         # 针对 tetris.py 的 pytest 测试（headless）
├── generate_sounds.py     # 音效生成脚本（纯 stdlib）
├── sounds/                # 9 个生成好的 WAV 音效
│   ├── move.wav / rotate.wav / soft_drop.wav / hard_drop.wav
│   ├── line_clear.wav / tetris_clear.wav
│   ├── level_up.wav / game_over.wav / hold.wav
├── setup.py               # py2app 打包配置
├── build_app.sh           # macOS 一键构建脚本
├── CLAUDE.md              # 给 AI 助手的项目说明
└── README.md
```

### 核心架构（`tetris.py`）

| 模块 | 职责 | 行数范围 |
|------|------|----------|
| 常量 | 网格尺寸、颜色、`SHAPES`、`WALL_KICKS` | 7-95 |
| `GameState` | 4 个状态：TITLE / PLAYING / PAUSED / GAME_OVER | 98-102 |
| `Button` | 带 hover 效果的 UI 按钮 | 105-128 |
| `Piece` | 方块位置 + 旋转态，`cells()` 计算世界坐标 | 131-149 |
| `TetrisGame` | 游戏逻辑 + 渲染（核心类） | 152-892 |

---

## 🛠 关键依赖

| 包 | 用途 | 必需 |
|------|------|------|
| `pygame` | 图形版渲染 + 音频 | 仅 `tetris.py` |
| `pytest` | 运行测试 | 仅开发 |
| `py2app` | macOS 打包 | 仅打包 |
| stdlib（`curses` / `wave` / `random` / `json`） | 终端版 + 音效生成 + 持久化 | ✅ |

---

## 🗺 路线图

- [ ] T-Spin Triple 与 Mini T-Spin 区分
- [ ] B2B（Back-to-Back）连击加分
- [ ] Combo 系统
- [ ] 多平台中文字体回退（当前硬编码 macOS `stheitimedium`）
- [ ] 抽离 input / logic / render 为独立模块
- [x] 增加 `tetris.py` 的单元测试（已完成 — 32 个测试，含 Hold/T-Spin/Level-up 回归）

---

## 📄 许可证

MIT License — 自由使用、修改、分发。

---

## 🙏 致谢

- 旋转 / 踢墙规则参考 [Tetris SRS Guideline](https://tetris.wiki/Super_Rotation_System)
- 计分规则参考 [Tetris Scoring](https://tetris.wiki/Scoring)

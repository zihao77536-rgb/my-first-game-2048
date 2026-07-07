# -*- coding: utf-8 -*-
"""
2048 —— 用 Pygame 做的完整小游戏（分场景音乐版）
================================================
功能：
  · 主菜单（开始游戏 / 玩法说明 / 退出）
  · 完整的 2048 玩法（移动、合并、随机生成、计分）
  · 方块滑动 + 合并/出现的弹跳动画
  · 分场景音乐：菜单曲 / 游戏曲 / 胜利小调 / 结束小调
  · 滑动、合并音效
  · 胜利、失败判定，最高分本地保存
操作：
  · 方向键 ↑↓←→ 或 W A S D 移动
  · M 键：开 / 关声音
  · ESC 返回菜单
运行：在终端里输入  python main.py

声音文件（放在与本脚本同一目录，缺文件也不会崩溃）：
  slide.wav  merge.wav  bgm_menu.wav  bgm_game.wav  win.wav  lose.wav
"""

import pygame
import sys
import random
import math
import os

# ============================================================
#  一、基本参数与配色
# ============================================================
WIDTH, HEIGHT = 500, 660

GRID = 4
CELL_SIZE = 100
GAP = 12
BOARD_LEFT = 20
BOARD_TOP = 165

BG_COLOR = (250, 248, 239)
BOARD_COLOR = (187, 173, 160)
EMPTY_CELL = (205, 193, 180)
TITLE_COLOR = (119, 110, 101)
TEXT_DARK = (119, 110, 101)
WHITE = (249, 246, 242)

ACCENT = (143, 122, 102)
ACCENT_HOVER = (158, 137, 116)
BTN2 = (214, 205, 194)
BTN2_HOVER = (224, 215, 204)

TILE_COLORS = {
    2:    ((238, 228, 218), (119, 110, 101)),
    4:    ((237, 224, 200), (119, 110, 101)),
    8:    ((242, 177, 121), (249, 246, 242)),
    16:   ((245, 149, 99),  (249, 246, 242)),
    32:   ((246, 124, 95),  (249, 246, 242)),
    64:   ((246, 94, 59),   (249, 246, 242)),
    128:  ((237, 207, 114), (249, 246, 242)),
    256:  ((237, 204, 97),  (249, 246, 242)),
    512:  ((237, 200, 80),  (249, 246, 242)),
    1024: ((237, 197, 63),  (249, 246, 242)),
    2048: ((237, 194, 46),  (249, 246, 242)),
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BEST_FILE = os.path.join(BASE_DIR, "best_score.txt")

# ============================================================
#  二、字体加载
# ============================================================
pygame.font.init()


def _find_cjk_font():
    for name in ["microsoftyahei", "msyh", "yahei", "simhei", "simsun", "dengxian"]:
        path = pygame.font.match_font(name)
        if path:
            return path
    return None


FONT_PATH = _find_cjk_font()
_font_cache = {}


def get_font(size, bold=True):
    key = (size, bold)
    if key not in _font_cache:
        if FONT_PATH:
            f = pygame.font.Font(FONT_PATH, size)
            f.set_bold(bold)
        else:
            f = pygame.font.SysFont(None, size, bold=bold)
        _font_cache[key] = f
    return _font_cache[key]


# ============================================================
#  三、游戏核心逻辑
# ============================================================
def new_board():
    board = [[0] * GRID for _ in range(GRID)]
    add_random_tile(board)
    add_random_tile(board)
    return board


def add_random_tile(board):
    empties = [(r, c) for r in range(GRID) for c in range(GRID) if board[r][c] == 0]
    if not empties:
        return None
    r, c = random.choice(empties)
    board[r][c] = 4 if random.random() < 0.1 else 2
    return (r, c)


def get_lines(direction):
    lines = []
    if direction == 'left':
        for r in range(GRID):
            lines.append([(r, c) for c in range(GRID)])
    elif direction == 'right':
        for r in range(GRID):
            lines.append([(r, c) for c in range(GRID - 1, -1, -1)])
    elif direction == 'up':
        for c in range(GRID):
            lines.append([(r, c) for r in range(GRID)])
    elif direction == 'down':
        for c in range(GRID):
            lines.append([(r, c) for r in range(GRID - 1, -1, -1)])
    return lines


def slide_line(values):
    non_zero = [(i, v) for i, v in enumerate(values) if v != 0]
    new_values = [0] * GRID
    moves = []
    gained = 0
    target = 0
    idx = 0
    while idx < len(non_zero):
        from_i, val = non_zero[idx]
        if idx + 1 < len(non_zero) and non_zero[idx + 1][1] == val:
            from_i2, _ = non_zero[idx + 1]
            new_values[target] = val * 2
            gained += val * 2
            moves.append((from_i, target, False))
            moves.append((from_i2, target, True))
            target += 1
            idx += 2
        else:
            new_values[target] = val
            moves.append((from_i, target, False))
            target += 1
            idx += 1
    return new_values, gained, moves


def move_board(board, direction):
    lines = get_lines(direction)
    new_board_ = [[0] * GRID for _ in range(GRID)]
    total_gained = 0
    all_moves = []
    moved = False
    for coords in lines:
        values = [board[r][c] for (r, c) in coords]
        new_values, gained, moves = slide_line(values)
        total_gained += gained
        for i, (r, c) in enumerate(coords):
            new_board_[r][c] = new_values[i]
        for (from_i, to_i, merged) in moves:
            from_coord = coords[from_i]
            to_coord = coords[to_i]
            all_moves.append((from_coord, to_coord, merged, values[from_i]))
            if from_coord != to_coord:
                moved = True
    return new_board_, total_gained, all_moves, moved


def board_won(board):
    return any(board[r][c] >= 2048 for r in range(GRID) for c in range(GRID))


def board_has_moves(board):
    for r in range(GRID):
        for c in range(GRID):
            if board[r][c] == 0:
                return True
            if c < GRID - 1 and board[r][c] == board[r][c + 1]:
                return True
            if r < GRID - 1 and board[r][c] == board[r + 1][c]:
                return True
    return False


def load_best():
    try:
        with open(BEST_FILE, "r") as f:
            return int(f.read().strip())
    except Exception:
        return 0


def save_best(best):
    try:
        with open(BEST_FILE, "w") as f:
            f.write(str(best))
    except Exception:
        pass


# ============================================================
#  四、绘制辅助
# ============================================================
def cell_center(r, c):
    x = BOARD_LEFT + GAP + c * (CELL_SIZE + GAP) + CELL_SIZE / 2
    y = BOARD_TOP + GAP + r * (CELL_SIZE + GAP) + CELL_SIZE / 2
    return (x, y)


def tile_colors(v):
    return TILE_COLORS.get(v, ((60, 58, 50), (249, 246, 242)))


def tile_font(v):
    d = len(str(v))
    size = 48 if d <= 2 else 40 if d == 3 else 32 if d == 4 else 24
    return get_font(size, bold=True)


def draw_tile(surface, value, center, scale=1.0):
    size = CELL_SIZE * scale
    if size < 1:
        return
    rect = pygame.Rect(0, 0, size, size)
    rect.center = center
    bg, fg = tile_colors(value)
    pygame.draw.rect(surface, bg, rect, border_radius=6)
    label = tile_font(value).render(str(value), True, fg)
    if scale != 1.0:
        w = max(1, int(label.get_width() * scale))
        h = max(1, int(label.get_height() * scale))
        label = pygame.transform.smoothscale(label, (w, h))
    surface.blit(label, label.get_rect(center=center))


def draw_board_base(surface):
    board_w = GRID * CELL_SIZE + (GRID + 1) * GAP
    pygame.draw.rect(surface, BOARD_COLOR,
                     (BOARD_LEFT, BOARD_TOP, board_w, board_w), border_radius=8)
    for r in range(GRID):
        for c in range(GRID):
            x = BOARD_LEFT + GAP + c * (CELL_SIZE + GAP)
            y = BOARD_TOP + GAP + r * (CELL_SIZE + GAP)
            pygame.draw.rect(surface, EMPTY_CELL,
                             (x, y, CELL_SIZE, CELL_SIZE), border_radius=6)


def draw_all_tiles(surface, board, skip=None):
    for r in range(GRID):
        for c in range(GRID):
            if board[r][c] != 0 and (skip is None or (r, c) not in skip):
                draw_tile(surface, board[r][c], cell_center(r, c))


def draw_score_box(surface, label, value, rect):
    pygame.draw.rect(surface, BOARD_COLOR, rect, border_radius=6)
    lbl = get_font(14, True).render(label, True, (238, 228, 218))
    surface.blit(lbl, lbl.get_rect(centerx=rect.centerx, top=rect.top + 6))
    val = get_font(24, True).render(str(value), True, WHITE)
    surface.blit(val, val.get_rect(centerx=rect.centerx, bottom=rect.bottom - 6))


def draw_header(surface, score, best, mouse_pos, restart_btn):
    title = get_font(64, True).render("2048", True, TITLE_COLOR)
    surface.blit(title, (25, 22))
    sub = get_font(18, False).render("合并方块，凑出 2048！", True, (150, 138, 125))
    surface.blit(sub, (27, 105))
    draw_score_box(surface, "分数", score, pygame.Rect(270, 22, 100, 58))
    draw_score_box(surface, "最高", best, pygame.Rect(380, 22, 100, 58))
    restart_btn.draw(surface, mouse_pos)


def draw_game_static(surface, board, score, best, mouse_pos, restart_btn, draw_tiles=True):
    surface.fill(BG_COLOR)
    draw_header(surface, score, best, mouse_pos, restart_btn)
    draw_board_base(surface)
    if draw_tiles:
        draw_all_tiles(surface, board)


def draw_footer(surface, sound_on):
    txt = "移动：方向键 / WASD      声音：{} · 按 M 切换".format("开" if sound_on else "关")
    label = get_font(16, False).render(txt, True, (170, 158, 145))
    surface.blit(label, label.get_rect(center=(WIDTH // 2, HEIGHT - 18)))


# ============================================================
#  五、按钮
# ============================================================
class Button:
    def __init__(self, rect, text, base, hover, text_color, font):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.base = base
        self.hover = hover
        self.text_color = text_color
        self.font = font

    def draw(self, surface, mouse_pos):
        color = self.hover if self.rect.collidepoint(mouse_pos) else self.base
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        label = self.font.render(self.text, True, self.text_color)
        surface.blit(label, label.get_rect(center=self.rect.center))

    def is_clicked(self, event):
        return (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and self.rect.collidepoint(event.pos))


# ============================================================
#  六、动画
# ============================================================
def ease_out_quad(p):
    return 1 - (1 - p) * (1 - p)


def ease_out_back(p):
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (p - 1) ** 3 + c1 * (p - 1) ** 2


def _pump_quit():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()


def animate_slide(screen, clock, board_before, moves, score, best, mouse_pos, restart_btn):
    duration = 90
    start = pygame.time.get_ticks()
    while True:
        t = (pygame.time.get_ticks() - start) / duration
        t = min(t, 1.0)
        _pump_quit()
        p = ease_out_quad(t)
        draw_game_static(screen, board_before, score, best, mouse_pos, restart_btn, draw_tiles=False)
        for (from_coord, to_coord, _merged, val) in moves:
            fr = cell_center(*from_coord)
            to = cell_center(*to_coord)
            cx = fr[0] + (to[0] - fr[0]) * p
            cy = fr[1] + (to[1] - fr[1]) * p
            draw_tile(screen, val, (cx, cy))
        pygame.display.flip()
        clock.tick(120)
        if t >= 1.0:
            break


def animate_pop(screen, clock, board, pop_cells, score, best, mouse_pos, restart_btn):
    if not pop_cells:
        return
    duration = 120
    skip = set(pop_cells.keys())
    start = pygame.time.get_ticks()
    while True:
        t = (pygame.time.get_ticks() - start) / duration
        t = min(t, 1.0)
        _pump_quit()
        draw_game_static(screen, board, score, best, mouse_pos, restart_btn, draw_tiles=False)
        draw_all_tiles(screen, board, skip=skip)
        for coord, kind in pop_cells.items():
            if kind == 'grow':
                scale = ease_out_back(t)
            else:
                scale = 1 + 0.18 * math.sin(t * math.pi)
            draw_tile(screen, board[coord[0]][coord[1]], cell_center(*coord), scale)
        pygame.display.flip()
        clock.tick(120)
        if t >= 1.0:
            break


# ============================================================
#  七、各种界面
# ============================================================
def draw_menu(surface, mouse_pos, best, play_btn, help_btn, quit_btn):
    surface.fill(BG_COLOR)
    title = get_font(96, True).render("2048", True, TITLE_COLOR)
    surface.blit(title, title.get_rect(center=(WIDTH // 2, 120)))

    demo = [2, 4, 8, 16]
    tsize, dgap = 64, 12
    total = len(demo) * tsize + (len(demo) - 1) * dgap
    startx = WIDTH // 2 - total // 2
    y = 210
    for i, v in enumerate(demo):
        cx = startx + i * (tsize + dgap) + tsize // 2
        rect = pygame.Rect(0, 0, tsize, tsize)
        rect.center = (cx, y)
        bg, fg = tile_colors(v)
        pygame.draw.rect(surface, bg, rect, border_radius=6)
        lbl = get_font(30, True).render(str(v), True, fg)
        surface.blit(lbl, lbl.get_rect(center=(cx, y)))

    sub = get_font(20, False).render("合并相同数字，挑战最高分", True, (150, 138, 125))
    surface.blit(sub, sub.get_rect(center=(WIDTH // 2, 280)))

    play_btn.draw(surface, mouse_pos)
    help_btn.draw(surface, mouse_pos)
    quit_btn.draw(surface, mouse_pos)

    best_lbl = get_font(20, True).render("最高分：{}".format(best), True, TEXT_DARK)
    surface.blit(best_lbl, best_lbl.get_rect(center=(WIDTH // 2, 588)))


def draw_help_overlay(surface, mouse_pos, back_btn):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((250, 248, 239, 236))
    surface.blit(overlay, (0, 0))

    title = get_font(40, True).render("玩法说明", True, TITLE_COLOR)
    surface.blit(title, title.get_rect(center=(WIDTH // 2, 90)))

    lines = [
        "· 方向键 或 W / A / S / D 移动方块",
        "· 相同数字相撞会合并，数值翻倍",
        "· 每次移动会随机冒出一个新方块",
        "· 拼出 2048 获胜，可继续挑战",
        "· 无法移动时游戏结束",
        "· 按 M 键 开 / 关声音",
        "",
        "小技巧：把大数字固定在角落，",
        "更容易滚起雪球！",
    ]
    y = 160
    fnt = get_font(21, False)
    for line in lines:
        txt = fnt.render(line, True, TEXT_DARK)
        surface.blit(txt, (45, y))
        y += 40
    back_btn.draw(surface, mouse_pos)


def draw_gameover_overlay(surface, mouse_pos, score, retry_btn, menu_btn):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((238, 228, 218, 212))
    surface.blit(overlay, (0, 0))
    t = get_font(56, True).render("游戏结束", True, (119, 110, 101))
    surface.blit(t, t.get_rect(center=(WIDTH // 2, 250)))
    s = get_font(26, True).render("本局得分：{}".format(score), True, (119, 110, 101))
    surface.blit(s, s.get_rect(center=(WIDTH // 2, 320)))
    retry_btn.draw(surface, mouse_pos)
    menu_btn.draw(surface, mouse_pos)


def draw_win_overlay(surface, mouse_pos, continue_btn, menu_btn):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((237, 194, 46, 205))
    surface.blit(overlay, (0, 0))
    t = get_font(60, True).render("你赢了！", True, WHITE)
    surface.blit(t, t.get_rect(center=(WIDTH // 2, 250)))
    s = get_font(28, True).render("成功拼出 2048！", True, WHITE)
    surface.blit(s, s.get_rect(center=(WIDTH // 2, 320)))
    continue_btn.draw(surface, mouse_pos)
    menu_btn.draw(surface, mouse_pos)


# ============================================================
#  八、声音加载
# ============================================================
def load_sound(filename, volume):
    """加载一个音效，失败就返回 None（游戏照常运行，只是没声）。"""
    try:
        s = pygame.mixer.Sound(os.path.join(BASE_DIR, filename))
        s.set_volume(volume)
        return s
    except Exception as e:
        print("提示：加载 {} 失败（{}），将静音运行。".format(filename, e))
        return None


# ============================================================
#  九、主程序
# ============================================================
def main():
    try:
        pygame.mixer.pre_init(44100, -16, 2, 512)
    except Exception:
        pass
    pygame.init()

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("我的 2048")
    clock = pygame.time.Clock()

    # 短音效
    slide_snd = load_sound("slide.wav", 0.35)
    merge_snd = load_sound("merge.wav", 0.55)
    win_snd = load_sound("win.wav", 0.6)      # 胜利小调（播一次）
    lose_snd = load_sound("lose.wav", 0.6)    # 结束小调（播一次）

    # 背景乐文件（用 music 流循环播放，同一时刻只放一首）
    BGM_FILES = {"menu": "bgm_menu.wav", "game": "bgm_game.wav"}
    BGM_VOLUME = 0.4

    sound_on = True
    current_track = None   # 当前正在循环的背景乐：'menu' / 'game' / None

    def play(snd):
        if sound_on and snd is not None:
            snd.play()

    def update_music(state):
        """根据当前场景切换背景乐；进入胜利/结束时停乐并播一次小调。"""
        nonlocal current_track
        desired = "menu" if state in ("menu", "help") else \
                  "game" if state == "play" else None
        if desired == current_track:
            return
        current_track = desired
        try:
            if desired in BGM_FILES:
                pygame.mixer.music.load(os.path.join(BASE_DIR, BGM_FILES[desired]))
                pygame.mixer.music.set_volume(BGM_VOLUME)
                pygame.mixer.music.play(-1)
                if not sound_on:
                    pygame.mixer.music.pause()
            else:
                pygame.mixer.music.fadeout(400)   # 淡出，留白给小调
        except Exception:
            pass
        # 进入结局，播放对应小调（一次）
        if state == "win":
            play(win_snd)
        elif state == "gameover":
            play(lose_snd)

    best = load_best()
    state = "menu"
    board = None
    score = 0
    won_shown = False

    cx = WIDTH // 2
    bw, bh = 240, 56
    play_btn = Button((cx - bw // 2, 330, bw, bh), "开始游戏", ACCENT, ACCENT_HOVER, WHITE, get_font(26, True))
    help_btn = Button((cx - bw // 2, 402, bw, bh), "玩法说明", BTN2, BTN2_HOVER, TEXT_DARK, get_font(24, True))
    quit_btn = Button((cx - bw // 2, 474, bw, bh), "退出游戏", BTN2, BTN2_HOVER, TEXT_DARK, get_font(24, True))

    restart_btn = Button((270, 92, 210, 40), "新游戏", ACCENT, ACCENT_HOVER, WHITE, get_font(20, True))

    ow, oh = 180, 50
    retry_btn = Button((cx - ow - 10, 380, ow, oh), "再来一局", ACCENT, ACCENT_HOVER, WHITE, get_font(22, True))
    continue_btn = Button((cx - ow - 10, 380, ow, oh), "继续挑战", ACCENT, ACCENT_HOVER, WHITE, get_font(22, True))
    menu_btn = Button((cx + 10, 380, ow, oh), "返回菜单", BTN2, BTN2_HOVER, TEXT_DARK, get_font(22, True))
    back_btn = Button((cx - 90, 560, 180, 46), "返回", ACCENT, ACCENT_HOVER, WHITE, get_font(22, True))

    while True:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_best(best)
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_m:
                sound_on = not sound_on
                try:
                    if sound_on:
                        pygame.mixer.music.unpause()
                    else:
                        pygame.mixer.music.pause()
                except Exception:
                    pass

            if state == "menu":
                if play_btn.is_clicked(event):
                    board = new_board(); score = 0; won_shown = False; state = "play"
                elif help_btn.is_clicked(event):
                    state = "help"
                elif quit_btn.is_clicked(event):
                    save_best(best); pygame.quit(); sys.exit()

            elif state == "help":
                if back_btn.is_clicked(event) or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    state = "menu"

            elif state == "play":
                if restart_btn.is_clicked(event):
                    board = new_board(); score = 0; won_shown = False
                elif event.type == pygame.KEYDOWN:
                    direction = None
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        direction = 'left'
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        direction = 'right'
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        direction = 'up'
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        direction = 'down'
                    elif event.key == pygame.K_ESCAPE:
                        state = "menu"

                    if direction:
                        new_b, gained, moves, moved = move_board(board, direction)
                        if moved:
                            play(slide_snd)
                            animate_slide(screen, clock, board, moves, score, best, mouse_pos, restart_btn)
                            board = new_b
                            score += gained
                            if score > best:
                                best = score
                            pop = {}
                            has_merge = False
                            for (_fc, tc, merged, _v) in moves:
                                if merged:
                                    pop[tc] = 'bump'
                                    has_merge = True
                            if has_merge:
                                play(merge_snd)
                            new_cell = add_random_tile(board)
                            if new_cell:
                                pop[new_cell] = 'grow'
                            animate_pop(screen, clock, board, pop, score, best, mouse_pos, restart_btn)
                            if not won_shown and board_won(board):
                                won_shown = True
                                save_best(best)
                                state = "win"
                            elif not board_has_moves(board):
                                save_best(best)
                                state = "gameover"

            elif state == "gameover":
                if retry_btn.is_clicked(event):
                    board = new_board(); score = 0; won_shown = False; state = "play"
                elif menu_btn.is_clicked(event):
                    state = "menu"

            elif state == "win":
                if continue_btn.is_clicked(event):
                    state = "play"
                elif menu_btn.is_clicked(event):
                    state = "menu"

        # 根据场景切换背景乐（内部会判断是否需要切换）
        update_music(state)

        # -------- 绘制 --------
        if state == "menu":
            draw_menu(screen, mouse_pos, best, play_btn, help_btn, quit_btn)
        elif state == "help":
            draw_menu(screen, mouse_pos, best, play_btn, help_btn, quit_btn)
            draw_help_overlay(screen, mouse_pos, back_btn)
        elif state == "play":
            draw_game_static(screen, board, score, best, mouse_pos, restart_btn, draw_tiles=True)
            draw_footer(screen, sound_on)
        elif state == "gameover":
            draw_game_static(screen, board, score, best, mouse_pos, restart_btn, draw_tiles=True)
            draw_footer(screen, sound_on)
            draw_gameover_overlay(screen, mouse_pos, score, retry_btn, menu_btn)
        elif state == "win":
            draw_game_static(screen, board, score, best, mouse_pos, restart_btn, draw_tiles=True)
            draw_footer(screen, sound_on)
            draw_win_overlay(screen, mouse_pos, continue_btn, menu_btn)

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()
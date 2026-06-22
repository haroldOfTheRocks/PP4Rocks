import tkinter as tk
import random

COLS = 10
ROWS = 20
CELL = 30
PANEL = 180

BG = '#0d0d1a'
GRID_COLOR = '#1a1a2e'

PIECES = {
    'I': ('#00FFFF', [[0, 0, 0, 0],
                      [1, 1, 1, 1],
                      [0, 0, 0, 0],
                      [0, 0, 0, 0]]),
    'O': ('#FFFF00', [[1, 1],
                      [1, 1]]),
    'T': ('#CC00FF', [[0, 1, 0],
                      [1, 1, 1],
                      [0, 0, 0]]),
    'S': ('#00FF00', [[0, 1, 1],
                      [1, 1, 0],
                      [0, 0, 0]]),
    'Z': ('#FF2020', [[1, 1, 0],
                      [0, 1, 1],
                      [0, 0, 0]]),
    'J': ('#4040FF', [[1, 0, 0],
                      [1, 1, 1],
                      [0, 0, 0]]),
    'L': ('#FF8000', [[0, 0, 1],
                      [1, 1, 1],
                      [0, 0, 0]]),
}

LINE_SCORES = {1: 100, 2: 300, 3: 500, 4: 800}


def rotate_cw(matrix):
    return [list(row) for row in zip(*matrix[::-1])]


def cells(matrix, x, y):
    return [
        (x + c, y + r)
        for r, row in enumerate(matrix)
        for c, val in enumerate(row)
        if val
    ]


class Piece:
    def __init__(self, name):
        self.name = name
        self.color, base = PIECES[name]
        self.matrix = [row[:] for row in base]
        # Spawn centered at top
        mat_w = len(self.matrix[0])
        self.x = (COLS - mat_w) // 2
        self.y = 0

    def rotated(self):
        p = Piece.__new__(Piece)
        p.name = self.name
        p.color = self.color
        p.matrix = rotate_cw(self.matrix)
        p.x = self.x
        p.y = self.y
        return p

    def moved(self, dx, dy):
        p = Piece.__new__(Piece)
        p.name = self.name
        p.color = self.color
        p.matrix = self.matrix
        p.x = self.x + dx
        p.y = self.y + dy
        return p

    def cells(self):
        return cells(self.matrix, self.x, self.y)


class Tetris:
    def __init__(self, root):
        self.root = root
        self.root.title('Tetris')
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        total_w = COLS * CELL + PANEL
        total_h = ROWS * CELL
        self.canvas = tk.Canvas(root, width=total_w, height=total_h, bg=BG,
                                highlightthickness=0)
        self.canvas.pack()

        self.root.bind('<Left>', lambda e: self.try_move(self.current.moved(-1, 0)))
        self.root.bind('<Right>', lambda e: self.try_move(self.current.moved(1, 0)))
        self.root.bind('<Down>', lambda e: self.soft_drop())
        self.root.bind('<Up>', lambda e: self.try_move(self.current.rotated()))
        self.root.bind('<space>', lambda e: self.hard_drop())
        self.root.bind('<p>', lambda e: self.toggle_pause())
        self.root.bind('<P>', lambda e: self.toggle_pause())
        self.root.bind('<r>', lambda e: self.new_game())
        self.root.bind('<R>', lambda e: self.new_game())

        self._after_id = None
        self.new_game()

    # ------------------------------------------------------------------ setup

    def new_game(self):
        if self._after_id:
            self.root.after_cancel(self._after_id)
            self._after_id = None
        self.board = [[None] * COLS for _ in range(ROWS)]
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.paused = False
        self.over = False
        self._bag = []
        self.next_piece = self._next_from_bag()
        self.current = self._spawn()
        self._tick()

    def _next_from_bag(self):
        if not self._bag:
            self._bag = list(PIECES.keys())
            random.shuffle(self._bag)
        return Piece(self._bag.pop())

    def _spawn(self):
        p = self.next_piece
        self.next_piece = self._next_from_bag()
        return p

    # ------------------------------------------------------------------ logic

    def _valid(self, piece):
        for x, y in piece.cells():
            if x < 0 or x >= COLS or y >= ROWS:
                return False
            if y >= 0 and self.board[y][x] is not None:
                return False
        return True

    def try_move(self, new_piece):
        if self.over or self.paused:
            return
        if self._valid(new_piece):
            self.current = new_piece
            self._redraw()

    def soft_drop(self):
        if self.over or self.paused:
            return
        moved = self.current.moved(0, 1)
        if self._valid(moved):
            self.current = moved
            self.score += 1
        else:
            self._lock()
        self._redraw()

    def hard_drop(self):
        if self.over or self.paused:
            return
        while True:
            moved = self.current.moved(0, 1)
            if self._valid(moved):
                self.current = moved
                self.score += 2
            else:
                break
        self._lock()
        self._redraw()

    def _lock(self):
        for x, y in self.current.cells():
            if y >= 0:
                self.board[y][x] = self.current.color
        self._clear_lines()
        self.current = self._spawn()
        if not self._valid(self.current):
            self.over = True

    def _clear_lines(self):
        full = [r for r in range(ROWS) if all(self.board[r][c] is not None for c in range(COLS))]
        if not full:
            return
        for r in full:
            del self.board[r]
            self.board.insert(0, [None] * COLS)
        n = len(full)
        self.score += LINE_SCORES.get(n, 0) * self.level
        self.lines_cleared += n
        self.level = self.lines_cleared // 10 + 1

    def _ghost(self):
        g = self.current
        while self._valid(g.moved(0, 1)):
            g = g.moved(0, 1)
        return g

    def _speed(self):
        return max(100, 700 - (self.level - 1) * 60)

    def toggle_pause(self):
        if self.over:
            return
        self.paused = not self.paused
        if not self.paused:
            self._tick()
        self._redraw()

    # ------------------------------------------------------------------ game loop

    def _tick(self):
        if not self.over and not self.paused:
            moved = self.current.moved(0, 1)
            if self._valid(moved):
                self.current = moved
            else:
                self._lock()
            self._redraw()
            if not self.over:
                self._after_id = self.root.after(self._speed(), self._tick)

    # ------------------------------------------------------------------ drawing

    def _redraw(self):
        c = self.canvas
        c.delete('all')

        # Background
        c.create_rectangle(0, 0, COLS * CELL, ROWS * CELL, fill=BG, outline='')

        # Grid lines
        for r in range(ROWS + 1):
            c.create_line(0, r * CELL, COLS * CELL, r * CELL, fill=GRID_COLOR)
        for col in range(COLS + 1):
            c.create_line(col * CELL, 0, col * CELL, ROWS * CELL, fill=GRID_COLOR)

        # Board cells
        for r in range(ROWS):
            for col in range(COLS):
                color = self.board[r][col]
                if color:
                    self._draw_cell(col, r, color)

        # Ghost piece
        ghost = self._ghost()
        if not self.over:
            for x, y in ghost.cells():
                if y >= 0:
                    self._draw_cell(x, y, self.current.color, ghost=True)

        # Current piece
        if not self.over:
            for x, y in self.current.cells():
                if y >= 0:
                    self._draw_cell(x, y, self.current.color)

        # Side panel separator
        px = COLS * CELL
        c.create_rectangle(px, 0, px + PANEL, ROWS * CELL, fill='#111122', outline='')
        c.create_line(px, 0, px, ROWS * CELL, fill='#334', width=2)

        # Score panel
        self._draw_panel(px)

        # Overlays
        if self.over:
            self._draw_overlay('GAME OVER', 'Press R to restart')
        elif self.paused:
            self._draw_overlay('PAUSED', 'Press P to resume')

    def _draw_cell(self, col, row, color, ghost=False):
        x1 = col * CELL + 1
        y1 = row * CELL + 1
        x2 = x1 + CELL - 2
        y2 = y1 + CELL - 2
        if ghost:
            self.canvas.create_rectangle(x1, y1, x2, y2,
                                          outline=color, fill='', width=2)
        else:
            self.canvas.create_rectangle(x1, y1, x2, y2,
                                          fill=color, outline='#000', width=1)
            # Highlight bevel
            self.canvas.create_line(x1, y1, x2 - 1, y1, fill='#ffffff44')
            self.canvas.create_line(x1, y1, x1, y2 - 1, fill='#ffffff44')

    def _draw_panel(self, px):
        c = self.canvas
        pad = 12
        x = px + pad

        def label(text, y, size=11, color='#aaaacc'):
            c.create_text(x, y, text=text, anchor='nw', fill=color,
                          font=('Courier', size, 'bold'))

        label('TETRIS', 18, size=16, color='#ffffff')
        c.create_line(px + pad, 44, px + PANEL - pad, 44, fill='#334', width=1)

        label('SCORE', 58, color='#7788aa')
        label(str(self.score), 76, size=13, color='#ffffff')

        label('LEVEL', 108, color='#7788aa')
        label(str(self.level), 126, size=13, color='#ffffff')

        label('LINES', 158, color='#7788aa')
        label(str(self.lines_cleared), 176, size=13, color='#ffffff')

        # Next piece preview
        label('NEXT', 218, color='#7788aa')
        c.create_rectangle(px + pad, 240, px + PANEL - pad, 330,
                           fill='#0d0d1a', outline='#334')
        self._draw_preview(px + pad + 10, 248)

        # Controls
        label('CONTROLS', ROWS * CELL - 170, color='#556677')
        controls = [
            ('← →', 'Move'),
            ('↑', 'Rotate'),
            ('↓', 'Soft drop'),
            ('SPC', 'Hard drop'),
            ('P', 'Pause'),
            ('R', 'Restart'),
        ]
        for i, (key, action) in enumerate(controls):
            y = ROWS * CELL - 150 + i * 20
            c.create_text(x, y, text=f'{key:>4} {action}', anchor='nw',
                          fill='#445566', font=('Courier', 8))

    def _draw_preview(self, ox, oy):
        p = self.next_piece
        mat = p.matrix
        cell = 22
        # Center in preview box
        mat_w = len(mat[0]) * cell
        mat_h = len(mat) * cell
        box_w = PANEL - 24 - 20
        box_h = 90
        start_x = ox + (box_w - mat_w) // 2
        start_y = oy + (box_h - mat_h) // 2
        for r, row in enumerate(mat):
            for col, val in enumerate(row):
                if val:
                    x1 = start_x + col * cell + 1
                    y1 = start_y + r * cell + 1
                    x2 = x1 + cell - 2
                    y2 = y1 + cell - 2
                    self.canvas.create_rectangle(x1, y1, x2, y2,
                                                  fill=p.color, outline='#000')

    def _draw_overlay(self, title, subtitle):
        cx = (COLS * CELL) // 2
        cy = (ROWS * CELL) // 2
        self.canvas.create_rectangle(cx - 120, cy - 50, cx + 120, cy + 50,
                                      fill='#000000cc', outline='#ffffff44')
        self.canvas.create_text(cx, cy - 16, text=title, fill='#ffffff',
                                 font=('Courier', 18, 'bold'))
        self.canvas.create_text(cx, cy + 16, text=subtitle, fill='#aaaacc',
                                 font=('Courier', 10))


def main():
    root = tk.Tk()
    Tetris(root)
    root.mainloop()


if __name__ == '__main__':
    main()

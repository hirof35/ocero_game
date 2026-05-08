import tkinter as tk
from tkinter import messagebox
import random
import copy

# 設定
EMPTY = 0
BLACK = 1
WHITE = -1
SIZE = 8
CELL_SIZE = 60

# 上級AI用の評価表（重み付け）
WEIGHTS = [
    [100, -40,  20,   5,   5,  20, -40, 100],
    [-40, -80,  -1,  -1,  -1,  -1, -80, -40],
    [ 20,  -1,   5,   1,   1,   5,  -1,  20],
    [  5,  -1,   1,   0,   0,   1,  -1,   5],
    [  5,  -1,   1,   0,   0,   1,  -1,   5],
    [ 20,  -1,   5,   1,   1,   5,  -1,  20],
    [-40, -80,  -1,  -1,  -1,  -1, -80, -40],
    [100, -40,  20,   5,   5,  20, -40, 100]
]

class OthelloGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Python オセロ (難易度選択)")
        
        # --- UIパネル ---
        self.top_frame = tk.Frame(root)
        self.top_frame.pack(pady=5)
        
        # 難易度選択用の変数とメニュー
        self.difficulty = tk.StringVar(value="Normal")
        tk.Label(self.top_frame, text="難易度:").pack(side=tk.LEFT)
        diff_menu = tk.OptionMenu(self.top_frame, self.difficulty, "Easy", "Normal", "Hard")
        diff_menu.pack(side=tk.LEFT, padx=5)
        
        tk.Button(self.top_frame, text="リセット", command=self.reset_game).pack(side=tk.LEFT, padx=5)
        tk.Button(self.top_frame, text="待った", command=self.undo).pack(side=tk.LEFT, padx=5)

        self.score_label = tk.Label(root, text="", font=("Helvetica", 12))
        self.score_label.pack()
        
        self.canvas = tk.Canvas(root, width=SIZE*CELL_SIZE, height=SIZE*CELL_SIZE, bg="#2e7d32")
        self.canvas.pack(padx=10, pady=10)
        self.canvas.bind("<Button-1>", self.on_click)
        
        self.reset_game()

    def reset_game(self):
        self.board = [[EMPTY] * SIZE for _ in range(SIZE)]
        self.board[3][3], self.board[4][4] = WHITE, WHITE
        self.board[3][4], self.board[4][3] = BLACK, BLACK
        self.current_player = BLACK
        self.history = []
        self.draw_board()

    def undo(self):
        if len(self.history) >= 1:
            last_state = self.history.pop()
            self.board = last_state["board"]
            self.current_player = last_state["player"]
            self.draw_board()

    def draw_board(self):
        self.canvas.delete("all")
        for i in range(SIZE + 1):
            self.canvas.create_line(0, i*CELL_SIZE, SIZE*CELL_SIZE, i*CELL_SIZE, fill="#1b5e20")
            self.canvas.create_line(i*CELL_SIZE, 0, i*CELL_SIZE, SIZE*CELL_SIZE, fill="#1b5e20")
        
        for r in range(SIZE):
            for c in range(SIZE):
                x, y = c * CELL_SIZE + 30, r * CELL_SIZE + 30
                if self.board[r][c] == BLACK:
                    self.canvas.create_oval(x-24, y-24, x+24, y+24, fill="black")
                elif self.board[r][c] == WHITE:
                    self.canvas.create_oval(x-24, y-24, x+24, y+24, fill="white")
        
        # ガイド表示
        if self.current_player == BLACK:
            for r, c in self.get_valid_moves(BLACK):
                cx, cy = c * CELL_SIZE + 30, r * CELL_SIZE + 30
                self.canvas.create_oval(cx-4, cy-4, cx+4, cy+4, fill="#1b5e20", outline="")
        
        b_count = sum(row.count(BLACK) for row in self.board)
        w_count = sum(row.count(WHITE) for row in self.board)
        self.score_label.config(text=f"黒: {b_count}  白: {w_count} ({self.difficulty.get()} AI)")

    def get_flippable_stones(self, row, col, player):
        if self.board[row][col] != EMPTY: return []
        flippable = []
        for dr, dc in [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]:
            r, c = row + dr, col + dc
            temp = []
            while 0 <= r < SIZE and 0 <= c < SIZE and self.board[r][c] == -player:
                temp.append((r, c))
                r, c = r + dr, c + dc
            if 0 <= r < SIZE and 0 <= c < SIZE and self.board[r][c] == player:
                flippable.extend(temp)
        return flippable

    def get_valid_moves(self, player):
        return [(r, c) for r in range(SIZE) for c in range(SIZE) if self.get_flippable_stones(r, c, player)]

    def ai_turn(self):
        valid_moves = self.get_valid_moves(WHITE)
        if not valid_moves:
            self.current_player = BLACK
            self.draw_board()
            return

        level = self.difficulty.get()
        if level == "Easy":
            move = random.choice(valid_moves)
        elif level == "Normal":
            corners = [m for m in valid_moves if m in [(0,0), (0,7), (7,0), (7,7)]]
            move = random.choice(corners) if corners else random.choice(valid_moves)
        else: # Hard: 評価表を使用
            # 最も重みが高い場所を選ぶ（同点ならランダム）
            best_score = -999
            best_moves = []
            for r, c in valid_moves:
                score = WEIGHTS[r][c]
                if score > best_score:
                    best_score = score
                    best_moves = [ (r, c) ]
                elif score == best_score:
                    best_moves.append( (r, c) )
            move = random.choice(best_moves)

        self.apply_move(move[0], move[1], WHITE)
        self.current_player = BLACK
        self.draw_board()
        self.check_game_over()

    def apply_move(self, r, c, player):
        stones = self.get_flippable_stones(r, c, player)
        self.board[r][c] = player
        for fr, fc in stones: self.board[fr][fc] = player

    def on_click(self, event):
        if self.current_player != BLACK: return
        c, r = event.x // CELL_SIZE, event.y // CELL_SIZE
        if (r, c) in self.get_valid_moves(BLACK):
            state = {"board": copy.deepcopy(self.board), "player": BLACK}
            self.history.append(state)
            self.apply_move(r, c, BLACK)
            self.current_player = WHITE
            self.draw_board()
            self.root.after(500, self.ai_turn)

    def check_game_over(self):
        if not self.get_valid_moves(BLACK) and not self.get_valid_moves(WHITE):
            b = sum(row.count(BLACK) for row in self.board)
            w = sum(row.count(WHITE) for row in self.board)
            msg = "引き分け" if b==w else ("黒の勝ち" if b>w else "白の勝ち")
            messagebox.showinfo("終了", f"黒:{b} 白:{w}\n{msg}")

if __name__ == "__main__":
    root = tk.Tk()
    app = OthelloGUI(root)
    root.mainloop()

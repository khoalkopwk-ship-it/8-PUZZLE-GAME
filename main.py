"""
Điểm chạy chương trình.
"""

import tkinter as tk

from game import EightPuzzleGame


if __name__ == "__main__":
    root = tk.Tk()
    app = EightPuzzleGame(root)
    root.mainloop()

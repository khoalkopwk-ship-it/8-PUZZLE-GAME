"""
Class EightPuzzleGame dựng giao diện chính và điều khiển trò chơi 8 Puzzle.

Bố cục hiện tại:
- Bên trái: bàn chơi + trạng thái ngắn gọn + kết quả tìm kiếm.
- Bên phải: trạng thái đích + thông tin game + điều khiển solver.
- Phần diện tích còn lại bên phải dành riêng cho mô phỏng thuật toán.
"""

import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from config import (
    APP_BG,
    BOARD_AREA_SIZE,
    BOARD_EMPTY_BG,
    BOARD_TILE_BG,
    BUTTON_NUMBER_ACTIVE,
    BUTTON_NUMBER_BG,
    BUTTON_RANDOM_ACTIVE,
    BUTTON_RANDOM_BG,
    BUTTON_UPLOAD_ACTIVE,
    BUTTON_UPLOAD_BG,
    CARD_BG,
    CARD_BORDER,
    GOAL_AREA_SIZE,
    GOAL_EMPTY_BG,
    GOAL_TILE_BG,
    GRID_SIZE,
    TEXT_BLUE,
    TEXT_DARK,
    TEXT_MUTED,
    WINDOW_HEIGHT,
    WINDOW_TITLE,
    WINDOW_WIDTH,
)
from image_utils import Image, ImageTk, PIL_AVAILABLE, prepare_image_for_grid
from puzzle_logic import (
    create_goal_state,
    create_random_state,
    generate_solvable_state,
    get_state_after_move,
)
from search_ui import SearchPanel
from solver import solve_with_algorithm
from widgets import RoundedFrame


class EightPuzzleGame:
    """Lớp chính quản lý game và kết nối UI với solver."""

    def __init__(self, root):
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.root.resizable(False, False)
        self.root.configure(bg=APP_BG)

        self.size = GRID_SIZE
        self.board_area_size = BOARD_AREA_SIZE
        self.goal_area_size = GOAL_AREA_SIZE
        self.tile_size = self.board_area_size // self.size
        self.goal_tile_size = self.goal_area_size // self.size

        self.moves = 0
        self.start_time = time.time()
        self.running = True
        self.animating = False
        self.puzzle_mode = "number"

        self.goal_state = create_goal_state(self.size)
        self.current_state = self.goal_state
        self.initial_state = self.current_state
        self.initial_goal_state = self.goal_state

        self.last_search_result = None
        self.solution_path = []
        self.solution_states = []

        self.source_image = None
        self.board_images = {}
        self.goal_images = {}

        self.center_window()
        self.configure_ttk_styles()
        self.build_ui()
        self.randomize_board()
        self.bind_keys()
        self.update_timer()

    def center_window(self):
        """Căn giữa cửa sổ ứng dụng trên màn hình."""
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (WINDOW_WIDTH // 2)
        y = (screen_height // 2) - (WINDOW_HEIGHT // 2)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")

    def configure_ttk_styles(self):
        """Cấu hình style cho ttk widgets."""
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TNotebook", background=CARD_BG, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(12, 8), font=("Segoe UI", 10, "bold"))
        style.configure("Treeview", rowheight=26, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
        style.configure("TCombobox", padding=4)

    def build_ui(self):
        """Tạo toàn bộ giao diện."""
        header_frame = tk.Frame(self.root, bg=APP_BG)
        header_frame.pack(fill="x", pady=(12, 6))

        title = tk.Label(
            header_frame,
            text="8 PUZZLE",
            font=("Segoe UI", 28, "bold"),
            fg=TEXT_DARK,
            bg=APP_BG,
        )
        title.pack()

        self.subtitle = tk.Label(
            header_frame,
            text="Sử dụng thuật toán BFS | DFS | UCS | Greedy | A*",
            font=("Segoe UI", 12),
            fg=TEXT_MUTED,
            bg=APP_BG,
        )
        self.subtitle.pack(pady=(4, 0))

        main_container = tk.Frame(self.root, bg=APP_BG)
        main_container.pack(fill="both", expand=True, padx=16, pady=(4, 16))

        self.create_left_card(main_container)
        self.create_right_card(main_container)

        self.draw_board()
        self.draw_goal()

    def create_left_card(self, parent):
        """Khung bên trái chứa bảng chơi chính và kết quả tìm kiếm."""
        left_card = RoundedFrame(
            parent,
            width=500,
            height=760,
            radius=28,
            bg=APP_BG,
            color=CARD_BG,
            border=CARD_BORDER,
        )
        left_card.pack(side="left", padx=(0, 12), pady=6)

        self.board_title = tk.Label(
            left_card.inner,
            text="BẢNG CHƠI 3 x 3",
            font=("Segoe UI", 16, "bold"),
            fg=TEXT_DARK,
            bg=CARD_BG,
        )
        self.board_title.pack(pady=(14, 10))

        self.board_frame = tk.Frame(
            left_card.inner,
            width=self.board_area_size,
            height=self.board_area_size,
            bg=BOARD_EMPTY_BG,
        )
        self.board_frame.pack(pady=(0, 12))
        self.board_frame.pack_propagate(False)

        quick_info = tk.Frame(left_card.inner, bg="#F7FAFD")
        quick_info.pack(fill="x", padx=22, pady=(0, 10))

        self.status_label = tk.Label(
            quick_info,
            text="Sẵn sàng. Bấm 'Chạy giải tự động' để xem lời giải.",
            font=("Segoe UI", 10, "bold"),
            fg=TEXT_MUTED,
            bg="#F7FAFD",
            wraplength=self.board_area_size - 44,
            justify="left",
        )
        self.status_label.pack(anchor="w", padx=14, pady=10)

        self.left_result_container = tk.Frame(left_card.inner, bg=CARD_BG)
        self.left_result_container.pack(fill="x", padx=22, pady=(0, 10))

    def create_right_card(self, parent):
        """Khung bên phải chứa goal, điều khiển và khu vực mô phỏng."""
        right_card = RoundedFrame(
            parent,
            width=960,
            height=760,
            radius=28,
            bg=APP_BG,
            color=CARD_BG,
            border=CARD_BORDER,
        )
        right_card.pack(side="right", padx=(12, 0), pady=6)

        top_row = tk.Frame(right_card.inner, bg=CARD_BG)
        top_row.pack(fill="x", pady=(10, 6))

        goal_box = tk.Frame(top_row, bg=CARD_BG)
        goal_box.pack(side="left", padx=(8, 18), anchor="n")

        goal_title = tk.Label(
            goal_box,
            text="TRẠNG THÁI ĐÍCH",
            font=("Segoe UI", 14, "bold"),
            fg=TEXT_DARK,
            bg=CARD_BG,
        )
        goal_title.pack(pady=(0, 8))

        self.goal_frame = tk.Frame(
            goal_box,
            width=self.goal_area_size,
            height=self.goal_area_size,
            bg=GOAL_EMPTY_BG,
        )
        self.goal_frame.pack()
        self.goal_frame.pack_propagate(False)

        self.mode_label = tk.Label(
            goal_box,
            text="Chế độ: Số | Lưới: 3 x 3",
            font=("Segoe UI", 11, "bold"),
            fg=TEXT_BLUE,
            bg=CARD_BG,
        )
        self.mode_label.pack(pady=(10, 0))

        side_info = tk.Frame(top_row, bg=CARD_BG)
        side_info.pack(side="left", fill="both", expand=True)

        self.create_info_panel(side_info)
        self.create_basic_buttons(side_info)

        self.visual_host = tk.Frame(right_card.inner, bg=CARD_BG)
        self.visual_host.pack(fill="both", expand=True, padx=10, pady=(6, 10))

        self.search_panel = SearchPanel(
            control_parent=side_info,
            result_parent=self.left_result_container,
            visual_parent=self.visual_host,
            on_auto_solve=self.run_auto_solver,
            on_replay_solution=self.replay_solution,
        )

    def create_info_panel(self, parent):
        """Hiển thị thông tin cơ bản của game."""
        info_box = tk.Frame(parent, bg="#F7FAFD")
        info_box.pack(fill="x", pady=(0, 10))

        self.move_label = tk.Label(
            info_box,
            text="Số bước: 0",
            font=("Segoe UI", 12, "bold"),
            fg=TEXT_BLUE,
            bg="#F7FAFD",
        )
        self.move_label.pack(anchor="w", padx=14, pady=(10, 4))

        self.time_label = tk.Label(
            info_box,
            text="Thời gian: 00:00",
            font=("Segoe UI", 12, "bold"),
            fg=TEXT_BLUE,
            bg="#F7FAFD",
        )
        self.time_label.pack(anchor="w", padx=14, pady=(0, 4))

    def create_basic_buttons(self, parent):
        """Các nút thao tác cơ bản của game."""
        button_box = tk.Frame(parent, bg=CARD_BG)
        button_box.pack(fill="x", pady=(0, 10))

        self.upload_btn = self.create_button(
            button_box,
            "Upload ảnh",
            self.upload_image,
            BUTTON_UPLOAD_BG,
            BUTTON_UPLOAD_ACTIVE,
        )
        self.upload_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.number_btn = self.create_button(
            button_box,
            "Chơi bằng số",
            self.switch_to_number_mode,
            BUTTON_NUMBER_BG,
            BUTTON_NUMBER_ACTIVE,
        )
        self.number_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.random_btn = self.create_button(
            button_box,
            "Làm mới",
            self.randomize_board_with_random_goal,
            BUTTON_RANDOM_BG,
            BUTTON_RANDOM_ACTIVE,
        )
        self.random_btn.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        self.restore_btn = self.create_button(
            button_box,
            "Khôi phục trạng thái",
            self.restore_initial_state,
            BUTTON_NUMBER_BG,
            BUTTON_NUMBER_ACTIVE,
        )
        self.restore_btn.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="ew")

        for col in range(3):
            button_box.grid_columnconfigure(col, weight=1)

    def create_button(self, parent, text, command, bg, active_bg):
        """Tạo nút chức năng dùng chung để giao diện đồng nhất."""
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI", 10, "bold"),
            fg="#FFFFFF",
            bg=bg,
            activebackground=active_bg,
            activeforeground="#FFFFFF",
            bd=0,
            cursor="hand2",
            height=2,
        )

    def bind_keys(self):
        """Gán phím điều khiển cho trò chơi."""
        key_map = {
            "<Up>": "up",
            "<Down>": "down",
            "<Left>": "left",
            "<Right>": "right",
            "w": "up",
            "W": "up",
            "s": "down",
            "S": "down",
            "a": "left",
            "A": "left",
            "d": "right",
            "D": "right",
        }

        for key, direction in key_map.items():
            self.root.bind(key, lambda event, move=direction: self.move(move))

    def refresh_static_labels(self):
        """Cập nhật các nhãn phụ thuộc chế độ chơi hiện tại."""
        mode_text = "Ảnh" if self.puzzle_mode == "image" else "Số"
        self.board_title.config(text=f"BẢNG CHƠI {self.size} x {self.size}")
        self.mode_label.config(text=f"Chế độ: {mode_text} | Lưới: {self.size} x {self.size}")

    def draw_board(self):
        """Vẽ lại bảng chơi hiện tại."""
        for widget in self.board_frame.winfo_children():
            widget.destroy()

        self.board_images.clear()

        for index, value in enumerate(self.current_state):
            row = index // self.size
            col = index % self.size
            x = col * self.tile_size + 4
            y = row * self.tile_size + 4
            width = self.tile_size - 8
            height = self.tile_size - 8

            if value == 0:
                tile = tk.Frame(self.board_frame, bg=BOARD_EMPTY_BG)
            elif self.puzzle_mode == "image" and self.source_image is not None:
                tile = self.create_image_tile(self.board_frame, value, width, height, is_goal=False)
            else:
                tile = tk.Label(
                    self.board_frame,
                    text=str(value),
                    font=("Segoe UI", 27, "bold"),
                    fg="#FFFFFF",
                    bg=BOARD_TILE_BG,
                    relief="flat",
                )

            tile.place(x=x, y=y, width=width, height=height)
            tile.bind("<Button-1>", lambda event, idx=index: self.handle_tile_click(idx))

    def draw_goal(self):
        """Vẽ trạng thái đích ở khung bên phải."""
        for widget in self.goal_frame.winfo_children():
            widget.destroy()

        self.goal_images.clear()

        for index, value in enumerate(self.goal_state):
            row = index // self.size
            col = index % self.size
            x = col * self.goal_tile_size + 2
            y = row * self.goal_tile_size + 2
            width = self.goal_tile_size - 4
            height = self.goal_tile_size - 4

            if value == 0:
                tile = tk.Frame(self.goal_frame, bg=GOAL_EMPTY_BG)
            elif self.puzzle_mode == "image" and self.source_image is not None:
                tile = self.create_image_tile(self.goal_frame, value, width, height, is_goal=True)
            else:
                tile = tk.Label(
                    self.goal_frame,
                    text=str(value),
                    font=("Segoe UI", 15, "bold"),
                    fg="#FFFFFF",
                    bg=GOAL_TILE_BG,
                    relief="flat",
                )

            tile.place(x=x, y=y, width=width, height=height)

    def create_image_tile(self, parent, value, width, height, is_goal=False):
        """Tạo một ô ảnh từ ảnh gốc."""
        image_index = value - 1
        image_row = image_index // self.size
        image_col = image_index % self.size

        crop_size = self.board_area_size // self.size
        left = image_col * crop_size
        top = image_row * crop_size
        right = left + crop_size
        bottom = top + crop_size

        piece = self.source_image.crop((left, top, right, bottom)).resize((width, height))
        photo = ImageTk.PhotoImage(piece)

        if is_goal:
            self.goal_images[value] = photo
        else:
            self.board_images[value] = photo

        return tk.Label(parent, image=photo, bg=CARD_BG, relief="flat")

    def handle_tile_click(self, index):
        """Cho phép người chơi click ô cạnh ô trống để di chuyển."""
        if not self.running or self.animating:
            return

        zero_index = self.current_state.index(0)
        zero_row = zero_index // self.size
        zero_col = zero_index % self.size
        tile_row = index // self.size
        tile_col = index % self.size

        if abs(zero_row - tile_row) + abs(zero_col - tile_col) != 1:
            return

        state_list = list(self.current_state)
        state_list[zero_index], state_list[index] = state_list[index], state_list[zero_index]
        self.current_state = tuple(state_list)
        self.after_successful_move()

    def move(self, direction):
        """Xử lý di chuyển bằng bàn phím."""
        if not self.running or self.animating:
            return

        new_state = get_state_after_move(self.current_state, direction, self.size)
        if new_state is None:
            return

        self.current_state = new_state
        self.after_successful_move()

    def after_successful_move(self):
        """Cập nhật giao diện sau mỗi lần người chơi di chuyển hợp lệ."""
        self.moves += 1
        self.move_label.config(text=f"Số bước: {self.moves}")
        self.invalidate_old_solution()
        self.draw_board()
        self.check_win()

    def invalidate_old_solution(self):
        """Xóa lời giải cũ nếu người chơi đã thay đổi trạng thái bằng tay."""
        if self.last_search_result is None:
            return

        self.last_search_result = None
        self.solution_path = []
        self.solution_states = []
        self.search_panel.reset_result("Trạng thái đã thay đổi. Hãy chạy lại thuật toán nếu cần.")

    def upload_image(self):
        """Cho phép upload ảnh từ máy tính để tạo puzzle dạng ảnh."""
        if not PIL_AVAILABLE:
            messagebox.showerror(
                "Thiếu thư viện Pillow",
                "Chức năng upload ảnh cần Pillow.\n\nHãy cài bằng lệnh:\npython -m pip install pillow",
            )
            return

        file_path = filedialog.askopenfilename(
            title="Chọn ảnh để tạo puzzle",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif"),
                ("All files", "*.*"),
            ],
        )

        if not file_path:
            return

        try:
            image = Image.open(file_path).convert("RGB")
            self.source_image = prepare_image_for_grid(image, self.board_area_size)
            self.puzzle_mode = "image"
            self.goal_state = create_goal_state(self.size)
            self.randomize_board()
            self.status_label.config(text="Đã upload ảnh thành công")
        except Exception as ex:
            messagebox.showerror("Lỗi upload ảnh", f"Không thể mở hoặc xử lý ảnh.\n\nChi tiết lỗi: {ex}")

    def switch_to_number_mode(self):
        """Chuyển trò chơi về chế độ số."""
        self.puzzle_mode = "number"
        self.source_image = None
        self.goal_state = create_goal_state(self.size)
        self.randomize_board()

    def save_initial_snapshot(self):
        """Lưu lại đề bài hiện tại để có thể khôi phục và so sánh thuật toán."""
        self.initial_state = self.current_state
        self.initial_goal_state = self.goal_state

    def restore_initial_state(self):
        """Khôi phục bảng chơi và goal về đúng đề bài của lần Làm mới gần nhất."""
        if self.animating:
            self.animating = False

        self.current_state = self.initial_state
        self.goal_state = self.initial_goal_state

        self.reset_game_counters()
        self.refresh_static_labels()
        self.draw_goal()
        self.draw_board()
        self.status_label.config(
            text="Đã khôi phục trạng thái ban đầu. Hãy chọn thuật toán khác để so sánh."
        )

    def reset_game_counters(self):
        """Đưa số bước, thời gian và trạng thái chạy về ban đầu."""
        self.running = True
        self.animating = False
        self.moves = 0
        self.start_time = time.time()
        self.move_label.config(text="Số bước: 0")
        self.reset_solver_state(summary="Chưa chạy thuật toán.", hide_visuals=True)

    def randomize_board(self):
        """Trộn mới bảng chơi theo goal chuẩn."""
        self.goal_state = create_goal_state(self.size)
        self.current_state = generate_solvable_state(self.goal_state, self.size)
        self.save_initial_snapshot()

        self.reset_game_counters()
        self.refresh_static_labels()
        self.draw_goal()
        self.draw_board()

    def randomize_board_with_random_goal(self):
        """Xử lý khi người chơi bấm nút Trộn mới."""
        if self.puzzle_mode == "image":
            self.goal_state = create_goal_state(self.size)
        else:
            self.goal_state = create_random_state(self.size)

        self.current_state = generate_solvable_state(self.goal_state, self.size)
        self.save_initial_snapshot()

        self.reset_game_counters()
        self.refresh_static_labels()
        self.draw_goal()
        self.draw_board()

    def run_auto_solver(self):
        """Chạy thuật toán đang chọn và tự trình diễn lời giải nếu tìm thấy."""
        if self.animating:
            return

        algorithm = self.search_panel.get_algorithm()
        heuristic_name = self.search_panel.get_heuristic()

        try:
            depth_limit = self.search_panel.get_depth_limit()
        except ValueError as ex:
            messagebox.showwarning("Giới hạn sâu không hợp lệ", str(ex))
            return

        self.status_label.config(text=f"Đang tìm lời giải bằng {algorithm}...")
        self.root.update_idletasks()

        try:
            result = solve_with_algorithm(
                algorithm,
                self.current_state,
                self.goal_state,
                self.size,
                depth_limit=depth_limit,
                heuristic_name=heuristic_name,
            )
        except Exception as ex:
            messagebox.showerror("Lỗi thuật toán", f"Không thể chạy thuật toán.\n\nChi tiết: {ex}")
            return

        self.last_search_result = result
        self.solution_path = result["path"]
        self.solution_states = result["solution_states"]
        self.search_panel.show_result(result)

        if not result["success"]:
            note = result.get("note") or "Không tìm thấy lời giải trong giới hạn hiện tại."
            self.status_label.config(text=f"{algorithm}: {note}")
            return

        self.status_label.config(
            text=f"{algorithm} đã tìm thấy lời giải: {result['depth']} bước. Đang trình diễn tự động..."
        )
        self.start_solution_animation(self.solution_states, algorithm)

    def start_solution_animation(self, states, algorithm):
        """Bắt đầu trình diễn lời giải trên bàn cờ."""
        if not states:
            return

        self.animating = True
        self.running = False
        self.current_state = states[0]
        self.draw_board()
        self.move_label.config(text="Số bước tự động: 0")
        self._animate_solution_step(states, 1, algorithm)

    def _animate_solution_step(self, states, index, algorithm):
        """Chạy từng bước trong lời giải."""
        if not self.animating:
            return

        if index >= len(states):
            self.animating = False
            self.running = False
            self.current_state = states[-1]
            self.draw_board()
            total_steps = len(states) - 1
            self.status_label.config(text=f"Đã giải tự động xong bằng {algorithm}. Bấm 'Làm mới' để chơi tiếp.")
            self.move_label.config(text=f"Số bước tự động: {total_steps}")
            return

        self.current_state = states[index]
        self.draw_board()
        self.move_label.config(text=f"Số bước tự động: {index}")
        self.status_label.config(text=f"Đang trình diễn bước {index}/{len(states) - 1}")
        self.root.after(450, lambda: self._animate_solution_step(states, index + 1, algorithm))

    def replay_solution(self):
        """Phát lại lời giải đã tìm được gần nhất."""
        if self.animating:
            return

        if not self.last_search_result or not self.last_search_result.get("success"):
            messagebox.showinfo("Chưa có lời giải", "Hãy chạy giải tự động thành công trước rồi mới phát lại.")
            return

        self.status_label.config(text="Đang phát lại lời giải gần nhất...")
        self.start_solution_animation(self.solution_states, self.last_search_result["algorithm"])

    def reset_solver_state(self, summary="Chưa chạy thuật toán.", hide_visuals=False):
        """Đưa dữ liệu solver về trạng thái ban đầu khi bàn chơi thay đổi."""
        self.last_search_result = None
        self.solution_path = []
        self.solution_states = []
        self.search_panel.reset_result(summary)

        if hide_visuals:
            self.search_panel.hide_visuals()

    def check_win(self):
        """Kiểm tra người chơi đã hoàn thành trò chơi chưa."""
        if self.current_state == self.goal_state:
            self.running = False
            elapsed = int(time.time() - self.start_time)
            minutes = elapsed // 60
            seconds = elapsed % 60
            messagebox.showinfo(
                "Chiến thắng!",
                "Bạn đã đạt giải cao trong thử thách ai thông minh hơn lớp 1!\n\n"
                f"Bạn đã hoàn thành Puzzle!\n\n"
                f"Lưới: {self.size} x {self.size}\n"
                f"Số bước: {self.moves}\n"
                f"Thời gian: {minutes:02d}:{seconds:02d}",
            )

    def update_timer(self):
        """Cập nhật đồng hồ thời gian mỗi giây."""
        if self.running and not self.animating:
            elapsed = int(time.time() - self.start_time)
            minutes = elapsed // 60
            seconds = elapsed % 60
            self.time_label.config(text=f"Thời gian: {minutes:02d}:{seconds:02d}")

        self.root.after(1000, self.update_timer)

"""
Module UI rieng cho phan chon thuat toan va mo phong tim kiem.

Game chinh chi can goi SearchPanel de:
- lay thuat toan dang chon,
- lay gioi han do sau cua DFS,
- hien thi ket qua solver,
- mo/dong bang mo phong khi can.
"""

import tkinter as tk
from tkinter import ttk

from config import CARD_BG, TEXT_DARK, TEXT_MUTED


class SearchPanel:
    """Khoi giao dien phu trach solver va phan mo phong thuat toan."""

    def __init__(
        self,
        control_parent,
        result_parent,
        visual_parent,
        on_auto_solve,
        on_replay_solution,
    ):
        self.on_auto_solve = on_auto_solve
        self.on_replay_solution = on_replay_solution

        self.algorithm_var = tk.StringVar(value="BFS")
        self.depth_var = tk.StringVar(value="20")
        self.heuristic_var = tk.StringVar(value="MANHATTAN")
        self.visuals_visible = False

        self.build_solver_panel(control_parent)
        self.build_result_panel(result_parent)
        self.build_visual_tabs(visual_parent)
        self.hide_visuals()

    def build_solver_panel(self, parent):
        """Tao khoi chon thuat toan va nut chay giai tu dong."""
        solver_box = tk.Frame(parent, bg="#F7FAFD")
        solver_box.pack(fill="x", pady=(0, 10))

        title = tk.Label(
            solver_box,
            text="CHON THUAT TOAN TIM KIEM",
            font=("Segoe UI", 11, "bold"),
            fg=TEXT_DARK,
            bg="#F7FAFD",
        )
        title.grid(row=0, column=0, columnspan=3, sticky="w", padx=14, pady=(10, 8))

        algo_label = tk.Label(
            solver_box,
            text="Thuat toan:",
            font=("Segoe UI", 10, "bold"),
            fg=TEXT_DARK,
            bg="#F7FAFD",
        )
        algo_label.grid(row=1, column=0, sticky="w", padx=14, pady=4)

        self.algorithm_combo = ttk.Combobox(
            solver_box,
            textvariable=self.algorithm_var,
            values=["BFS", "DFS", "UCS", "Greedy", "A*"],
            state="readonly",
            width=14,
        )
        self.algorithm_combo.grid(row=1, column=1, columnspan=2, sticky="ew", padx=(0, 14), pady=4)
        self.algorithm_combo.bind("<<ComboboxSelected>>", lambda event: self.update_depth_hint())

        depth_label = tk.Label(
            solver_box,
            text="Gioi han sau DFS:",
            font=("Segoe UI", 10, "bold"),
            fg=TEXT_DARK,
            bg="#F7FAFD",
        )
        depth_label.grid(row=2, column=0, sticky="w", padx=14, pady=4)

        self.depth_entry = tk.Entry(
            solver_box,
            textvariable=self.depth_var,
            font=("Segoe UI", 10),
            relief="solid",
            bd=1,
        )
        self.depth_entry.grid(row=2, column=1, columnspan=2, sticky="ew", padx=(0, 14), pady=4)

        heuristic_label = tk.Label(
            solver_box,
            text="Heuristic:",
            font=("Segoe UI", 10, "bold"),
            fg=TEXT_DARK,
            bg="#F7FAFD",
        )
        heuristic_label.grid(row=3, column=0, sticky="w", padx=14, pady=4)

        self.heuristic_combo = ttk.Combobox(
            solver_box,
            textvariable=self.heuristic_var,
            values=["MANHATTAN", "MISPLACED"],
            state="disabled",
            width=14,
        )
        self.heuristic_combo.grid(row=3, column=1, columnspan=2, sticky="ew", padx=(0, 14), pady=4)

        self.depth_hint_label = tk.Label(
            solver_box,
            text="BFS va UCS bo qua gioi han sau. DFS dung gia tri nay.",
            font=("Segoe UI", 9),
            fg=TEXT_MUTED,
            bg="#F7FAFD",
        )
        self.depth_hint_label.grid(row=4, column=0, columnspan=3, sticky="w", padx=14, pady=(2, 8))

        self.auto_solve_btn = self.create_button(
            solver_box,
            "Chạy giải tự động",
            self.on_auto_solve,
            "#0EA5A4",
            "#0B8A89",
        )
        self.auto_solve_btn.grid(row=5, column=0, padx=(14, 5), pady=(0, 10), sticky="ew")

        self.replay_btn = self.create_button(
            solver_box,
            "Phát lại lời giải",
            self.on_replay_solution,
            "#F59E0B",
            "#D97706",
        )
        self.replay_btn.grid(row=5, column=1, padx=5, pady=(0, 10), sticky="ew")

        self.toggle_visual_btn = self.create_button(
            solver_box,
            "Mở bảng mô phỏng",
            self.toggle_visuals,
            "#4F8EF7",
            "#3C79DE",
        )
        self.toggle_visual_btn.grid(row=5, column=2, padx=(5, 14), pady=(0, 10), sticky="ew")

        for col in range(3):
            solver_box.grid_columnconfigure(col, weight=1)

        self.update_depth_hint()

    def build_result_panel(self, parent):
        """Tao phan tom tat ket qua tim kiem, co con lan khi noi dung dai."""
        self.result_box = tk.Frame(parent, bg="#F7FAFD")
        self.result_box.pack(fill="x", padx=0, pady=(0, 8))

        title = tk.Label(
            self.result_box,
            text="KET QUA TIM KIEM",
            font=("Segoe UI", 11, "bold"),
            fg=TEXT_DARK,
            bg="#F7FAFD",
        )
        title.pack(anchor="w", padx=14, pady=(10, 6))

        summary_frame = tk.Frame(self.result_box, bg="#F7FAFD")
        summary_frame.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        self.result_text = tk.Text(
            summary_frame,
            height=6,
            wrap="word",
            font=("Segoe UI", 10),
            fg=TEXT_MUTED,
            bg="#F7FAFD",
            relief="flat",
            bd=0,
            padx=0,
            pady=0,
            cursor="arrow",
        )
        result_scroll = ttk.Scrollbar(summary_frame, orient="vertical", command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=result_scroll.set)

        self.result_text.grid(row=0, column=0, sticky="nsew")
        result_scroll.grid(row=0, column=1, sticky="ns")

        summary_frame.grid_rowconfigure(0, weight=1)
        summary_frame.grid_columnconfigure(0, weight=1)

        self.set_result_summary("Chua chay thuat toan.")

    def set_result_summary(self, text):
        """Cap nhat noi dung ket qua tim kiem trong o co con lan."""
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", text)
        self.result_text.configure(state="disabled")

    def build_visual_tabs(self, parent):
        """Tao notebook chua bang duyet va cay rut gon, mac dinh se an."""
        self.visual_container = tk.Frame(parent, bg=CARD_BG)

        self.tab_bar = tk.Frame(self.visual_container, bg=CARD_BG)
        self.tab_bar.pack(fill="x", padx=0, pady=(0, 0))

        self.active_tab = tk.StringVar(value="trace")

        self.trace_tab_button = tk.Button(
            self.tab_bar,
            text="Bang duyet trang thai",
            command=lambda: self.select_visual_tab("trace"),
            font=("Segoe UI", 11, "bold"),
            fg="#000000",
            bg="#FFFFFF",
            activebackground="#FFFFFF",
            relief="raised",
            bd=2,
            padx=16,
            pady=8,
            cursor="hand2",
        )
        self.trace_tab_button.pack(side="left", padx=(0, 2))

        self.tree_tab_button = tk.Button(
            self.tab_bar,
            text="Cay rut gon",
            command=lambda: self.select_visual_tab("tree"),
            font=("Segoe UI", 10, "bold"),
            fg="#000000",
            bg="#D8D2C6",
            activebackground="#D8D2C6",
            relief="raised",
            bd=1,
            padx=12,
            pady=5,
            cursor="hand2",
        )
        self.tree_tab_button.pack(side="left", padx=(0, 2))

        self.tab_content = tk.Frame(self.visual_container, bg=CARD_BG)
        self.tab_content.pack(fill="both", expand=True)

        self.trace_tab = tk.Frame(self.tab_content, bg=CARD_BG)
        self.tree_tab = tk.Frame(self.tab_content, bg=CARD_BG)

        self.create_trace_table(self.trace_tab)
        self.create_search_tree(self.tree_tab)

        self.select_visual_tab("trace")

    def create_trace_table(self, parent):
        """Bang hien thi tung trang thai duoc sinh/duyet."""
        wrapper = tk.Frame(parent, bg=CARD_BG)
        wrapper.pack(fill="both", expand=True, padx=8, pady=8)

        columns = ("step", "depth", "move", "state")
        self.trace_table = ttk.Treeview(wrapper, columns=columns, show="headings")
        self.trace_table.heading("step", text="Buoc")
        self.trace_table.heading("depth", text="Do sau")
        self.trace_table.heading("move", text="Move")
        self.trace_table.heading("state", text="Trang thai")

        self.trace_table.column("step", width=60, anchor="center")
        self.trace_table.column("depth", width=80, anchor="center")
        self.trace_table.column("move", width=70, anchor="center")
        self.trace_table.column("state", width=620, anchor="w")

        y_scroll = ttk.Scrollbar(wrapper, orient="vertical", command=self.trace_table.yview)
        x_scroll = ttk.Scrollbar(wrapper, orient="horizontal", command=self.trace_table.xview)
        self.trace_table.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.trace_table.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

        wrapper.grid_rowconfigure(0, weight=1)
        wrapper.grid_columnconfigure(0, weight=1)

    def create_search_tree(self, parent):
        """Treeview bieu dien mo hinh cay rut gon."""
        wrapper = tk.Frame(parent, bg=CARD_BG)
        wrapper.pack(fill="both", expand=True, padx=8, pady=8)

        note = tk.Label(
            wrapper,
            text="Cay chi hien thi mot phan trang thai dau tien de de quan sat.",
            font=("Segoe UI", 9),
            fg=TEXT_MUTED,
            bg=CARD_BG,
        )
        note.grid(row=0, column=0, sticky="w", pady=(0, 6))

        self.search_tree = ttk.Treeview(wrapper, show="tree")
        self.search_tree.grid(row=1, column=0, sticky="nsew")

        tree_scroll = ttk.Scrollbar(wrapper, orient="vertical", command=self.search_tree.yview)
        self.search_tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.grid(row=1, column=1, sticky="ns")

        wrapper.grid_rowconfigure(1, weight=1)
        wrapper.grid_columnconfigure(0, weight=1)

    def create_button(self, parent, text, command, bg, active_bg):
        """Tao button dong nhat style."""
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

    def update_depth_hint(self):
        """Cap nhat ghi chu cho o gioi han do sau va heuristic."""
        algorithm = self.algorithm_var.get().strip().upper()

        if algorithm == "DFS":
            self.depth_entry.config(state="normal")
            self.heuristic_combo.config(state="disabled")
            self.depth_hint_label.config(text="DFS dung gioi han sau de tranh di qua sau. Goi y: 15-30.")
        elif algorithm == "UCS":
            self.depth_entry.config(state="disabled")
            self.heuristic_combo.config(state="disabled")
            self.depth_hint_label.config(text="UCS bo qua gioi han sau va uu tien bang hang doi uu tien.")
        elif algorithm == "GREEDY":
            self.depth_entry.config(state="disabled")
            self.heuristic_combo.config(state="readonly")
            self.depth_hint_label.config(text="Greedy uu tien h(n) nho nhat. Chon MANHATTAN hoac MISPLACED.")
        elif algorithm == "A*":
            self.depth_entry.config(state="disabled")
            self.heuristic_combo.config(state="readonly")
            self.depth_hint_label.config(text="A* uu tien f(n) = g(n) + h(n). Chon MANHATTAN hoac MISPLACED.")
        else:
            self.depth_entry.config(state="disabled")
            self.heuristic_combo.config(state="disabled")
            self.depth_hint_label.config(text="BFS bo qua gioi han sau va uu tien so buoc ngan nhat.")

    def get_algorithm(self):
        """Lay thuat toan dang chon."""
        return self.algorithm_var.get().upper()

    def get_heuristic(self):
        """Lay heuristic dang chon cho Greedy va A*."""
        return self.heuristic_var.get()

    def get_depth_limit(self):
        """Doc gioi han sau tu o nhap."""
        raw = self.depth_var.get().strip()
        if raw == "":
            return 20

        try:
            value = int(raw)
        except ValueError as exc:
            raise ValueError("Gioi han sau phai la so nguyen.") from exc

        if value < 0:
            raise ValueError("Gioi han sau phai lon hon hoac bang 0.")

        return value

    def show_result(self, result):
        """Hien thi tom tat, bang duyet va cay rut gon."""
        success_text = "Tim thay loi giai" if result["success"] else "Chua tim thay loi giai"
        depth_limit_text = "-"

        if result.get("depth_limit") is not None and result["algorithm"] == "DFS":
            depth_limit_text = str(result["depth_limit"])

        heuristic_text = result.get("heuristic") or "-"
        path_text = " -> ".join(move.upper()[0] for move in result["path"]) if result["path"] else "Khong co"

        summary = (
            f"Thuat toan: {result['algorithm']} | Ket qua: {success_text}\n"
            f"Do dai loi giai: {result['depth']} buoc | "
            f"Do sau lon nhat da duyet: {result['max_depth']} | Gioi han sau DFS: {depth_limit_text}\n"
            f"Heuristic: {heuristic_text} | "
            f"So trang thai da ghi nhan: {result['visited_count']} | So nut da mo rong: {result['expanded_count']} | "
            f"Thoi gian: {result['elapsed_ms']} ms\n"
            f"Loi giai: {path_text}"
        )

        if result.get("note"):
            summary += f"\nGhi chu: {result['note']}"

        if not self.visuals_visible:
            summary += "\nBang mo phong dang an. Bam 'Mo bang mo phong' de xem bang duyet va cay rut gon."

        self.set_result_summary(summary)

        self.populate_trace_table(result["trace_rows"])
        self.populate_tree_view(result["tree_nodes"])

    def populate_trace_table(self, rows):
        """Nap du lieu vao bang duyet."""
        for item in self.trace_table.get_children():
            self.trace_table.delete(item)

        for row in rows:
            self.trace_table.insert(
                "",
                "end",
                values=(
                    row["step"],
                    row["depth"],
                    row["move"],
                    row["state"],
                ),
            )

    def populate_tree_view(self, nodes):
        """Nap du lieu cay rut gon vao tree view."""
        for item in self.search_tree.get_children():
            self.search_tree.delete(item)

        for node in nodes:
            parent = node["parent"] if node["parent"] else ""
            self.search_tree.insert(parent, "end", iid=node["id"], text=node["text"])

        for item in self.search_tree.get_children():
            self.search_tree.item(item, open=True)

    def reset_result(self, summary="Chua chay thuat toan."):
        """Dua bang ket qua ve trang thai rong khi trang thai puzzle thay doi."""
        for item in self.trace_table.get_children():
            self.trace_table.delete(item)

        for item in self.search_tree.get_children():
            self.search_tree.delete(item)

        self.set_result_summary(summary)

    def toggle_visuals(self):
        """Mo hoac dong bang mo phong."""
        if self.visuals_visible:
            self.hide_visuals()
        else:
            self.show_visuals()

    def show_visuals(self):
        """Hien bang duyet va cay rut gon."""
        if self.visuals_visible:
            return

        self.visual_container.pack(fill="both", expand=True, padx=0, pady=0)
        self.toggle_visual_btn.config(text="An bang mo phong")
        self.visuals_visible = True

    def hide_visuals(self):
        """An bang duyet va cay rut gon."""
        if self.visual_container.winfo_ismapped():
            self.visual_container.pack_forget()

        self.toggle_visual_btn.config(text="Mở bảng mô phỏng")
        self.visuals_visible = False

    def select_visual_tab(self, tab_name):
        """Chon tab mo phong va lam tab dang chon lon hon tab con lai."""
        self.active_tab.set(tab_name)

        self.trace_tab.pack_forget()
        self.tree_tab.pack_forget()

        if tab_name == "trace":
            self.trace_tab.pack(fill="both", expand=True)

            self.trace_tab_button.config(
                font=("Segoe UI", 11, "bold"),
                bg="#FFFFFF",
                activebackground="#FFFFFF",
                bd=2,
                padx=16,
                pady=8,
            )

            self.tree_tab_button.config(
                font=("Segoe UI", 10, "bold"),
                bg="#D8D2C6",
                activebackground="#D8D2C6",
                bd=1,
                padx=12,
                pady=5,
            )

        elif tab_name == "tree":
            self.tree_tab.pack(fill="both", expand=True)

            self.tree_tab_button.config(
                font=("Segoe UI", 11, "bold"),
                bg="#FFFFFF",
                activebackground="#FFFFFF",
                bd=2,
                padx=16,
                pady=8,
            )

            self.trace_tab_button.config(
                font=("Segoe UI", 10, "bold"),
                bg="#D8D2C6",
                activebackground="#D8D2C6",
                bd=1,
                padx=12,
                pady=5,
            )

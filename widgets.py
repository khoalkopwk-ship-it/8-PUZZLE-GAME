"""
Chứa các widget phụ dùng lại trong giao diện.

Hiện tại chỉ có RoundedFrame để tạo khung bo góc giống giao diện ban đầu.
Tách riêng widget này giúp file game.py gọn hơn, có thể nâng cấp.
"""

import tkinter as tk


class RoundedFrame(tk.Canvas):
    """
    Khung bo góc dùng Canvas.

    Canvas được dùng để vẽ nền bo góc rồi đặt một Frame con tên là `inner` vào bên trong.
    Các thành phần giao diện khác sẽ được đặt vào `inner`.
    """

    def __init__(self, parent, width, height, radius=24, bg="#EEF3F8", color="#FFFFFF", border="#D6E0EC"):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=bg,
            highlightthickness=0,
            bd=0,
        )
        self.width = width
        self.height = height
        self.radius = radius
        self.color = color
        self.border = border

        self.draw_rounded_rect()

        # Frame con để chứa Label, Button, Frame... như một Frame bình thường.
        self.inner = tk.Frame(self, bg=color)
        self.create_window(
            width // 2,
            height // 2,
            window=self.inner,
            width=width - 24,
            height=height - 24,
        )

    def draw_rounded_rect(self):
        """Vẽ hình chữ nhật bo góc bằng các cung tròn và hình chữ nhật nhỏ."""
        r = self.radius
        w = self.width
        h = self.height

        # Lớp viền ngoài
        self.create_arc(1, 1, 2 * r, 2 * r, start=90, extent=90, fill=self.border, outline=self.border)
        self.create_arc(w - 2 * r, 1, w - 1, 2 * r, start=0, extent=90, fill=self.border, outline=self.border)
        self.create_arc(1, h - 2 * r, 2 * r, h - 1, start=180, extent=90, fill=self.border, outline=self.border)
        self.create_arc(w - 2 * r, h - 2 * r, w - 1, h - 1, start=270, extent=90, fill=self.border, outline=self.border)
        self.create_rectangle(r, 1, w - r, h - 1, fill=self.border, outline=self.border)
        self.create_rectangle(1, r, w - 1, h - r, fill=self.border, outline=self.border)

        # Lớp nền chính bên trong
        pad = 2
        self.create_arc(pad, pad, 2 * r, 2 * r, start=90, extent=90, fill=self.color, outline=self.color)
        self.create_arc(w - 2 * r, pad, w - pad, 2 * r, start=0, extent=90, fill=self.color, outline=self.color)
        self.create_arc(pad, h - 2 * r, 2 * r, h - pad, start=180, extent=90, fill=self.color, outline=self.color)
        self.create_arc(w - 2 * r, h - 2 * r, w - pad, h - pad, start=270, extent=90, fill=self.color, outline=self.color)
        self.create_rectangle(r, pad, w - r, h - pad, fill=self.color, outline=self.color)
        self.create_rectangle(pad, r, w - pad, h - r, fill=self.color, outline=self.color)


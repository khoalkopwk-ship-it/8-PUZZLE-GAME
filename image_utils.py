"""
Chứa các hàm xử lý ảnh bằng Pillow.

Tách riêng phần ảnh giúp game.py không bị dài và dễ thay đổi cách xử lý ảnh
"""

try:
    from PIL import Image, ImageOps, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    Image = None
    ImageOps = None
    ImageTk = None
    PIL_AVAILABLE = False


def prepare_image_for_grid(image, target_size):
    """
    Resize/crop ảnh thành hình vuông target_size x target_size.

    ImageOps.fit giữ ảnh luôn vừa khít khung vuông, giúp các mảnh puzzle sau khi
    cắt ra có kích thước đều nhau.
    """
    return ImageOps.fit(
        image,
        (target_size, target_size),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )

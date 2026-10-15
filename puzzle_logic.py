"""
Logic thuần của 8 Puzzle.

chứa các thao tác nền tảng:
- tạo trạng thái đích / trạng thái ngẫu nhiên,
- sinh nước đi,
- định dạng trạng thái.

"""

import random


MOVE_ORDER = ("up", "down", "left", "right")

MOVE_LABELS = {
    "up": "U",
    "down": "D",
    "left": "L",
    "right": "R",
}


def create_goal_state(size):
    """Tạo trạng thái đích chuẩn: 1, 2, ..., N*N-1, 0."""
    return tuple(list(range(1, size * size)) + [0])


def create_random_state(size):
    """Tạo một trạng thái ngẫu nhiên gồm các số từ 1 đến N*N-1 và ô trống 0."""
    state = list(range(1, size * size)) + [0]
    random.shuffle(state)
    return tuple(state)


def get_state_after_move(state, direction, size):
    """
    Trả về trạng thái mới sau khi di chuyển ô trống.

    Quy ước direction là hướng di chuyển của ô trống:
    - up: ô trống đi lên
    - down: ô trống đi xuống
    - left: ô trống đi sang trái
    - right: ô trống đi sang phải

    Nếu hướng đi không hợp lệ, hàm trả về None.
    """
    zero_index = state.index(0)
    zero_row = zero_index // size
    zero_col = zero_index % size

    target_row = zero_row
    target_col = zero_col

    if direction == "up":
        target_row -= 1
    elif direction == "down":
        target_row += 1
    elif direction == "left":
        target_col -= 1
    elif direction == "right":
        target_col += 1
    else:
        return None

    if not (0 <= target_row < size and 0 <= target_col < size):
        return None

    target_index = target_row * size + target_col
    state_list = list(state)
    state_list[zero_index], state_list[target_index] = state_list[target_index], state_list[zero_index]
    return tuple(state_list)


def generate_neighbors(state, size, move_order=MOVE_ORDER):
    """Sinh danh sách (move, next_state) theo đúng thứ tự yêu cầu."""
    neighbors = []
    for move in move_order:
        next_state = get_state_after_move(state, move, size)
        if next_state is not None:
            neighbors.append((move, next_state))
    return neighbors


def generate_solvable_state(goal_state, size, shuffle_moves=12):
    """
    Tạo trạng thái chắc chắn giải được so với goal_state bằng cách đi ngẫu nhiên từ goal.

    Cách này phù hợp cho giao diện mô phỏng thuật toán vì trạng thái sinh ra thường
    không quá xa goal, giúp BFS / DFS / UCS chạy nhanh hơn khi trình diễn trên lớp.
    """
    current = goal_state
    previous = None

    for _ in range(shuffle_moves):
        neighbors = generate_neighbors(current, size)
        if previous is not None:
            filtered = [(move, state) for move, state in neighbors if state != previous]
            if filtered:
                neighbors = filtered

        _, next_state = random.choice(neighbors)
        previous, current = current, next_state

    if current == goal_state:
        return generate_solvable_state(goal_state, size, shuffle_moves + 1)

    return current


def format_state_inline(state, size):
    """Chuyển trạng thái thành chuỗi ngắn gọn dạng 123/405/678."""
    rows = []
    for row in range(size):
        segment = state[row * size:(row + 1) * size]
        rows.append("".join("_" if value == 0 else str(value) for value in segment))
    return "/".join(rows)


def build_solution_states(start, path, size):
    """Tạo danh sách trạng thái đi theo lời giải từ start đến goal."""
    states = [start]
    current = start

    for move in path:
        current = get_state_after_move(current, move, size)
        if current is None:
            break
        states.append(current)

    return states

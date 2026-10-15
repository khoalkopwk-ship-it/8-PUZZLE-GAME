"""
File solver.py chứa toàn bộ phần "giải tự động" cho trò chơi 8-puzzle.

Các thuật toán đang hỗ trợ:
- BFS: duyệt theo chiều rộng, tìm lời giải có ít bước nhất nếu mỗi bước có cùng chi phí.
- DFS: duyệt theo chiều sâu, có giới hạn độ sâu để tránh đi quá xa hoặc lặp vô hạn.
- UCS: duyệt theo tổng chi phí đường đi g(n), phù hợp khi mỗi bước có chi phí khác nhau.
- Greedy Best-First Search: chọn trạng thái có h(n) nhỏ nhất, tức trạng thái "trông có vẻ gần đích nhất".
- A*: chọn trạng thái có f(n) = g(n) + h(n) nhỏ nhất, kết hợp chi phí đã đi và ước lượng còn lại.

Quy ước dữ liệu:
- state/start/goal là tuple, ví dụ: (1, 2, 3, 4, 5, 6, 7, 8, 0).
- Ô trống được biểu diễn bằng số 0.
- size là kích thước cạnh bàn cờ, với 8-puzzle thông thường size = 3.
- path là danh sách các bước di chuyển, ví dụ: ["UP", "LEFT", ...].

Mỗi hàm giải thuật trả về dictionary có cùng cấu trúc để giao diện có thể:
- hiển thị số bước, số trạng thái đã duyệt, thời gian chạy,
- tạo bảng quá trình duyệt,
- tạo cây tìm kiếm rút gọn,
- trình diễn đường đi lời giải trên bàn cờ.
"""

from collections import deque
import heapq
import itertools
import time

from puzzle_logic import (
    MOVE_LABELS,
    build_solution_states,
    format_state_inline,
    generate_neighbors,
)


# Các nhãn heuristic dùng để hiển thị trên giao diện.
# Key bên trái là tên nội bộ trong code, value bên phải là chữ hiện trên UI.
HEURISTIC_LABELS = {
    "manhattan": "MANHATTAN",
    "misplaced": "MISPLACED",
}


def get_ucs_move_cost(next_depth):
    """
    Tính chi phí của một bước đi trong UCS.

    Tham số:
    - next_depth: độ sâu của trạng thái con sau khi đi thêm một bước.

    Ý nghĩa:
    - Trong code này, bước càng sâu thì chi phí bước đó càng lớn.
    - Bước đi ở độ sâu 1 có cost = 1, độ sâu 2 có cost = 2, ...
    - UI hiện chưa cần hiển thị chi phí chi tiết, nhưng UCS vẫn dùng giá trị này
      để ưu tiên trạng thái có tổng cost nhỏ nhất.
    """
    return max(1, next_depth)


def _goal_positions(goal, size):
    """
    Tạo bảng tra cứu vị trí đích của từng ô số.

    Ví dụ goal = (1, 2, 3, 4, 5, 6, 7, 8, 0), size = 3:
    - số 1 ở hàng 0, cột 0
    - số 2 ở hàng 0, cột 1
    - số 8 ở hàng 2, cột 1

    Hàm này giúp các heuristic không phải tìm lại vị trí đích của từng số nhiều lần.
    """
    positions = {}

    # enumerate(goal) cho biết mỗi ô đang nằm ở chỉ số nào trong tuple goal.
    for index, value in enumerate(goal):
        # Chuyển chỉ số 1 chiều thành tọa độ 2 chiều:
        # hàng = index // size, cột = index % size.
        positions[value] = (index // size, index % size)

    return positions


def _tile_distances(state, goal, size):
    """
    Tính khoảng cách theo hàng/cột giữa mỗi ô số hiện tại và vị trí đích của nó.

    Kết quả trả về là danh sách các cặp (dx, dy):
    - dx: số hàng bị lệch so với vị trí đích.
    - dy: số cột bị lệch so với vị trí đích.

    Lưu ý:
    - Bỏ qua ô trống 0 vì ô trống không được tính vào heuristic.
    - Danh sách (dx, dy) này đang được dùng cho Manhattan.
    """
    positions = _goal_positions(goal, size)
    distances = []

    for index, value in enumerate(state):
        # Không tính ô trống vào heuristic.
        if value == 0:
            continue

        # Tọa độ hiện tại của ô value.
        row = index // size
        col = index % size

        # Tọa độ đích của ô value.
        goal_row, goal_col = positions[value]

        # Lưu độ lệch tuyệt đối theo hàng và cột.
        distances.append((abs(row - goal_row), abs(col - goal_col)))

    return distances


def heuristic_manhattan(state, goal, size):
    """
    Heuristic MANHATTAN.

    Công thức cho mỗi ô:
    h = |hàng hiện tại - hàng đích| + |cột hiện tại - cột đích|

    Ý nghĩa:
    - Đo số bước ngang/dọc tối thiểu để đưa từng ô về đúng vị trí.
    - Đây là heuristic thường dùng nhất cho 8-puzzle.
    """
    return sum(dx + dy for dx, dy in _tile_distances(state, goal, size))




def heuristic_misplaced(state, goal, size):
    """
    Heuristic MISPLACED TILES.

    Cách tính:
    - So sánh từng ô của trạng thái hiện tại với trạng thái đích.
    - Mỗi ô số đang đặt sai vị trí được tính là 1.
    - Không tính ô trống 0.

    Ý nghĩa:
    - h(n) = số quân chưa nằm đúng vị trí.
    - Heuristic này đơn giản, dễ hiểu và thường yếu hơn Manhattan,
      nhưng rất phù hợp để so sánh sự khác biệt giữa Greedy và A*.
    """
    misplaced_count = 0

    for current_value, goal_value in zip(state, goal):
        if current_value != 0 and current_value != goal_value:
            misplaced_count += 1

    return misplaced_count


def normalize_heuristic_name(heuristic_name):
    """
    Chuẩn hóa tên heuristic lấy từ combobox giao diện.

    Giao diện hiện chỉ cho chọn 2 heuristic:
    - "MANHATTAN"
    - "MISPLACED"

    Nếu không nhận ra tên heuristic, mặc định dùng Manhattan để tránh lỗi.
    """
    raw = (heuristic_name or "manhattan").strip().lower()

    if "misplaced" in raw:
        return "misplaced"

    return "manhattan"


def calculate_heuristic(state, goal, size, heuristic_name="manhattan"):
    """
    Tính giá trị heuristic h(n) cho một trạng thái.

    Tham số:
    - state: trạng thái cần đánh giá.
    - goal: trạng thái đích.
    - size: kích thước bàn cờ.
    - heuristic_name: tên heuristic được chọn trên giao diện.

    Ý nghĩa trong thuật toán:
    - Greedy dùng trực tiếp h(n) để chọn trạng thái tiếp theo.
    - A* dùng h(n) kết hợp với g(n) để tính f(n) = g(n) + h(n).

    Các heuristic còn giữ lại:
    - Manhattan: tổng khoảng cách ngang/dọc của các ô so với vị trí đích.
    - Misplaced: số ô đang sai vị trí so với trạng thái đích.
    """
    heuristic_key = normalize_heuristic_name(heuristic_name)

    if heuristic_key == "misplaced":
        return heuristic_misplaced(state, goal, size)

    return heuristic_manhattan(state, goal, size)


def format_heuristic_value(value):
    """
    Định dạng giá trị h(n) hoặc f(n) để hiển thị gọn trên giao diện.

    Lý do cần hàm này:
    - Các heuristic hiện tại trả về số nguyên.
    - Vẫn giữ xử lý số thực để giao diện không bị lỗi nếu sau này bổ sung heuristic khác.
    """
    if isinstance(value, float) and not value.is_integer():
        return f"{value:.2f}"
    return str(int(value))


def get_heuristic_label(heuristic_name):
    """
    Lấy nhãn hiển thị của heuristic.

    Ví dụ:
    - key "manhattan" -> "MANHATTAN"
    - key "misplaced" -> "MISPLACED"
    """
    return HEURISTIC_LABELS[normalize_heuristic_name(heuristic_name)]


def _trace_row(step, depth, move, state, size):
    """
    Tạo một dòng dữ liệu cho bảng mô phỏng quá trình duyệt.

    Mỗi dòng gồm:
    - step: thứ tự trạng thái được phát hiện/đưa vào danh sách xét.
    - depth: độ sâu của trạng thái trong cây tìm kiếm.
    - move: bước di chuyển tạo ra trạng thái này.
    - state: trạng thái được format thành chuỗi dễ đọc.
    """
    return {
        "step": step,
        "depth": depth,
        "move": move,
        "state": format_state_inline(state, size),
    }


def _result(
    success,
    algorithm,
    start,
    size,
    path,
    visited_count,
    expanded_count,
    max_depth,
    trace_rows,
    tree_nodes,
    started_at,
    depth_limit=None,
    note="",
    heuristic=None,
):
    """
    Chuẩn hóa kết quả trả về cho tất cả thuật toán.

    Vì BFS, DFS, UCS, Greedy, A* đều trả về cùng một dạng dictionary,
    phần giao diện không cần xử lý riêng từng thuật toán.

    Các thông tin quan trọng:
    - success: có tìm được lời giải không.
    - path: danh sách bước đi từ start đến goal.
    - depth: số bước của lời giải.
    - visited_count: số trạng thái đã được phát hiện.
    - expanded_count: số trạng thái đã được mở rộng để sinh trạng thái con.
    - trace_rows: dữ liệu cho bảng duyệt.
    - tree_nodes: dữ liệu cho cây tìm kiếm rút gọn.
    - solution_states: danh sách trạng thái dùng để chạy animation lời giải.
    """
    # Tính thời gian chạy tính bằng mili-giây để hiển thị thống kê.
    elapsed_ms = int((time.time() - started_at) * 1000)

    # Nếu giải thành công, dựng toàn bộ trạng thái trên đường đi để chạy animation.
    # Nếu thất bại, chỉ trả về trạng thái đầu để UI không bị lỗi.
    solution_states = build_solution_states(start, path, size) if success else [start]

    return {
        "success": success,
        "algorithm": algorithm,
        "path": path,
        "depth": len(path),
        "depth_limit": depth_limit,
        "visited_count": visited_count,
        "expanded_count": expanded_count,
        "max_depth": max_depth,
        "trace_rows": trace_rows,
        "tree_nodes": tree_nodes,
        "elapsed_ms": elapsed_ms,
        "solution_states": solution_states,
        "note": note,
        "heuristic": heuristic,
    }


def _path_from_parents(parents, goal_state):
    """
    Truy vết đường đi lời giải từ trạng thái đích về trạng thái đầu.

    parents lưu theo dạng:
    parents[trạng_thái_con] = (trạng_thái_cha, bước_đi_từ_cha_đến_con, độ_sâu)

    Cách hoạt động:
    - Bắt đầu từ goal_state.
    - Lần lượt đi ngược về cha của nó.
    - Thu được danh sách bước đi bị ngược thứ tự.
    - Đảo ngược danh sách để có đường đi đúng từ start đến goal.
    """
    path = []

    # cursor bắt đầu từ trạng thái đích rồi lần lượt đi ngược về start.
    cursor = goal_state

    while parents[cursor][0] is not None:
        parent_state, move = parents[cursor][0], parents[cursor][1]

        # move là bước đi từ parent_state đến cursor.
        path.append(move)
        cursor = parent_state

    # Vì đang truy ngược từ goal về start nên cần đảo lại để có thứ tự đúng.
    return list(reversed(path))


def solve_bfs(start, goal, size, node_limit=200000, trace_limit=180, tree_limit=100):
    """
    BFS - Breadth-First Search.

    Nguyên lý:
    - Duyệt theo từng tầng của cây tìm kiếm.
    - Trạng thái nào được sinh trước sẽ được xét trước.
    - Dùng queue FIFO: thêm cuối hàng đợi, lấy đầu hàng đợi.

    Đặc điểm:
    - Nếu mỗi bước đi có chi phí như nhau, BFS tìm được lời giải có số bước ít nhất.
    - Nhược điểm là tốn bộ nhớ vì phải lưu nhiều trạng thái ở cùng một tầng.
    """
    started_at = time.time()

    # parents dùng để truy vết lời giải sau khi gặp goal.
    # start không có cha nên lưu (None, None, 0).
    parents = {start: (None, None, 0)}

    # BFS dùng hàng đợi FIFO: trạng thái vào trước được mở rộng trước.
    queue = deque([start])

    # visited tránh đưa cùng một trạng thái vào queue nhiều lần.
    visited = {start}

    # trace_rows và tree_nodes chỉ phục vụ giao diện mô phỏng.
    trace_rows = [_trace_row(1, 0, "Start", start, size)]
    tree_nodes = [{
        "id": "B0",
        "parent": "",
        "text": f"Start | d=0 | {format_state_inline(start, size)}",
    }]
    tree_ids = {start: "B0"}

    # Trường hợp đặc biệt: start đã là goal.
    if start == goal:
        return _result(
            True,
            "BFS",
            start,
            size,
            [],
            1,
            0,
            0,
            trace_rows,
            tree_nodes,
            started_at,
            note="Trang thai dau da la trang thai dich.",
        )

    step = 1
    expanded_count = 0
    max_depth = 0

    while queue:
        # Lấy trạng thái ở đầu hàng đợi để đảm bảo duyệt theo từng tầng.
        current = queue.popleft()
        current_depth = parents[current][2]
        expanded_count += 1

        # Sinh tất cả trạng thái con có thể đi được từ current.
        for move, neighbor in generate_neighbors(current, size):
            # Nếu trạng thái đã gặp rồi thì bỏ qua để tránh lặp.
            if neighbor in visited:
                continue

            visited.add(neighbor)
            child_depth = current_depth + 1
            max_depth = max(max_depth, child_depth)
            parents[neighbor] = (current, move, child_depth)

            # Đưa trạng thái con vào cuối hàng đợi để xét ở các lượt sau.
            queue.append(neighbor)

            step += 1
            if len(trace_rows) < trace_limit:
                trace_rows.append(_trace_row(step, child_depth, MOVE_LABELS[move], neighbor, size))

            if len(tree_nodes) < tree_limit:
                node_id = f"B{len(tree_ids)}"
                tree_ids[neighbor] = node_id
                tree_nodes.append({
                    "id": node_id,
                    "parent": tree_ids[current],
                    "text": f"{MOVE_LABELS[move]} | d={child_depth} | {format_state_inline(neighbor, size)}",
                })

            # BFS kiểm tra goal ngay khi sinh ra neighbor.
            # Vì BFS duyệt theo tầng, đây là đường đi ngắn nhất theo số bước.
            if neighbor == goal:
                path = _path_from_parents(parents, neighbor)
                return _result(
                    True,
                    "BFS",
                    start,
                    size,
                    path,
                    len(visited),
                    expanded_count,
                    max_depth,
                    trace_rows,
                    tree_nodes,
                    started_at,
                )

            # Giới hạn số trạng thái giúp chương trình không bị treo khi bài quá khó.
            if len(visited) >= node_limit:
                return _result(
                    False,
                    "BFS",
                    start,
                    size,
                    [],
                    len(visited),
                    expanded_count,
                    max_depth,
                    trace_rows,
                    tree_nodes,
                    started_at,
                    note=f"Da dung vi vuot gioi han {node_limit} trang thai.",
                )

    return _result(
        False,
        "BFS",
        start,
        size,
        [],
        len(visited),
        expanded_count,
        max_depth,
        trace_rows,
        tree_nodes,
        started_at,
        note="Khong tim thay loi giai.",
    )


def solve_ucs(start, goal, size, node_limit=200000, trace_limit=220, tree_limit=120):
    """
    Giải 8-puzzle bằng UCS - Uniform Cost Search.

    Nguyên lý:
    - Mỗi trạng thái có tổng chi phí g(n) từ start đến trạng thái đó.
    - Luôn mở rộng trạng thái có g(n) nhỏ nhất.
    - Dùng priority queue, tức heapq trong Python.

    Khác với BFS:
    - BFS ưu tiên theo số bước.
    - UCS ưu tiên theo tổng chi phí.
    - Nếu mọi bước có cùng cost = 1 thì UCS gần giống BFS.
    """
    started_at = time.time()

    # counter dùng để phá hòa khi nhiều trạng thái có cùng độ ưu tiên trong heap.
    # Nếu không có counter, heapq có thể phải so sánh tuple state khi cost bằng nhau.
    counter = itertools.count()

    # frontier là hàng đợi ưu tiên: (cost, depth, thứ_tự, state).
    # heapq luôn lấy phần tử có cost nhỏ nhất.
    frontier = [(0, 0, next(counter), start)]

    parents = {start: (None, None, 0)}

    # best_cost[state] lưu tổng chi phí nhỏ nhất đã biết từ start đến state.
    best_cost = {start: 0}
    best_depth = {start: 0}

    trace_rows = [_trace_row(1, 0, "Start", start, size)]
    tree_nodes = [{
        "id": "U0",
        "parent": "",
        "text": f"Start | d=0 | {format_state_inline(start, size)}",
    }]
    tree_ids = {start: "U0"}
    tree_counter = 1

    if start == goal:
        return _result(
            True,
            "UCS",
            start,
            size,
            [],
            1,
            0,
            0,
            trace_rows,
            tree_nodes,
            started_at,
            note="Trang thai dau da la trang thai dich.",
        )

    step = 1
    expanded_count = 0
    max_depth = 0

    while frontier:
        # Lấy trạng thái có tổng chi phí nhỏ nhất ra khỏi heap.
        current_cost, current_depth, _, current = heapq.heappop(frontier)

        # Nếu bản ghi trong heap đã cũ, tức sau đó đã tìm được đường rẻ hơn,
        # thì bỏ qua bản ghi cũ này.
        if current_cost != best_cost.get(current):
            continue

        expanded_count += 1

        if current == goal:
            path = _path_from_parents(parents, current)
            return _result(
                True,
                "UCS",
                start,
                size,
                path,
                len(best_cost),
                expanded_count,
                max_depth,
                trace_rows,
                tree_nodes,
                started_at,
            )

        for move, neighbor in generate_neighbors(current, size):
            child_depth = current_depth + 1

            # g(n) của trạng thái con = cost hiện tại + cost bước mới.
            child_cost = current_cost + get_ucs_move_cost(child_depth)

            # Chỉ cập nhật nếu tìm được đường đi rẻ hơn đến neighbor.
            if child_cost >= best_cost.get(neighbor, float("inf")):
                continue

            best_cost[neighbor] = child_cost
            best_depth[neighbor] = child_depth
            parents[neighbor] = (current, move, child_depth)
            max_depth = max(max_depth, child_depth)

            # Đưa vào heap để UCS luôn ưu tiên trạng thái có cost nhỏ nhất.
            heapq.heappush(frontier, (child_cost, child_depth, next(counter), neighbor))

            step += 1
            if len(trace_rows) < trace_limit:
                trace_rows.append(_trace_row(step, child_depth, MOVE_LABELS[move], neighbor, size))

            if len(tree_nodes) < tree_limit:
                parent_id = tree_ids.get(current, "")
                node_id = f"U{tree_counter}"
                tree_counter += 1
                tree_ids[neighbor] = node_id
                tree_nodes.append({
                    "id": node_id,
                    "parent": parent_id,
                    "text": f"{MOVE_LABELS[move]} | d={child_depth} | {format_state_inline(neighbor, size)}",
                })

            if len(best_cost) >= node_limit:
                return _result(
                    False,
                    "UCS",
                    start,
                    size,
                    [],
                    len(best_cost),
                    expanded_count,
                    max_depth,
                    trace_rows,
                    tree_nodes,
                    started_at,
                    note=f"Da dung vi vuot gioi han {node_limit} trang thai.",
                )

    return _result(
        False,
        "UCS",
        start,
        size,
        [],
        len(best_cost),
        expanded_count,
        max_depth,
        trace_rows,
        tree_nodes,
        started_at,
        note="Khong tim thay loi giai.",
    )


def solve_dfs(start, goal, size, depth_limit=25, trace_limit=180, tree_limit=100):
    """
    DFS - Depth-First Search có giới hạn độ sâu.

    Nguyên lý:
    - Đi sâu theo một nhánh trước.
    - Khi không thể đi tiếp hoặc chạm giới hạn độ sâu thì quay lui.
    - Dùng đệ quy và cơ chế backtracking.

    Đặc điểm:
    - Ít tốn bộ nhớ hơn BFS.
    - Không đảm bảo tìm lời giải ngắn nhất.
    - Cần depth_limit để tránh đi quá sâu hoặc chạy quá lâu.
    """
    started_at = time.time()

    trace_rows = [_trace_row(1, 0, "Start", start, size)]
    tree_nodes = [{
        "id": "D0",
        "parent": "",
        "text": f"Start | d=0 | {format_state_inline(start, size)}",
    }]

    # seen_unique đếm số trạng thái khác nhau đã từng xuất hiện trong quá trình DFS.
    seen_unique = {start}
    expanded_count = 0
    max_depth = 0
    step = 1
    tree_counter = 1
    found_path = None

    # path lưu các bước trên nhánh hiện tại.
    path = []

    # path_set giúp tránh đi vòng trong cùng một nhánh DFS.
    path_set = {start}

    def dfs(state, depth, tree_parent_id):
        """
        Hàm DFS đệ quy bên trong solve_dfs.

        Tham số:
        - state: trạng thái hiện tại.
        - depth: độ sâu hiện tại.
        - tree_parent_id: id của nút cha trong cây mô phỏng UI.
        """
        # nonlocal cho phép hàm con cập nhật biến nằm ở hàm solve_dfs bên ngoài.
        nonlocal expanded_count, max_depth, step, tree_counter, found_path

        expanded_count += 1
        max_depth = max(max_depth, depth)

        # Nếu trạng thái hiện tại là goal thì sao chép đường đi hiện tại làm lời giải.
        if state == goal:
            found_path = list(path)
            return True

        # Dừng nhánh hiện tại nếu đã đạt giới hạn độ sâu.
        if depth >= depth_limit:
            return False

        for move, neighbor in generate_neighbors(state, size):
            # Không đi lại trạng thái đã nằm trên nhánh hiện tại để tránh vòng lặp.
            if neighbor in path_set:
                continue

            child_depth = depth + 1
            seen_unique.add(neighbor)

            # Thử đi theo neighbor: thêm bước vào path và đánh dấu neighbor thuộc nhánh hiện tại.
            path.append(move)
            path_set.add(neighbor)
            step += 1

            if len(trace_rows) < trace_limit:
                trace_rows.append(_trace_row(step, child_depth, MOVE_LABELS[move], neighbor, size))

            child_tree_id = f"D{tree_counter}"
            tree_counter += 1
            if len(tree_nodes) < tree_limit:
                tree_nodes.append({
                    "id": child_tree_id,
                    "parent": tree_parent_id,
                    "text": f"{MOVE_LABELS[move]} | d={child_depth} | {format_state_inline(neighbor, size)}",
                })

            # Nếu nhánh con tìm thấy goal thì dừng toàn bộ DFS.
            if dfs(neighbor, child_depth, child_tree_id):
                return True

            # Backtracking: nếu nhánh con không dẫn đến goal thì rút bước vừa thử ra khỏi path.
            path.pop()
            path_set.remove(neighbor)

        return False

    dfs(start, 0, "D0")

    if found_path is not None:
        return _result(
            True,
            "DFS",
            start,
            size,
            found_path,
            len(seen_unique),
            expanded_count,
            max_depth,
            trace_rows,
            tree_nodes,
            started_at,
            depth_limit=depth_limit,
        )

    return _result(
        False,
        "DFS",
        start,
        size,
        [],
        len(seen_unique),
        expanded_count,
        max_depth,
        trace_rows,
        tree_nodes,
        started_at,
        depth_limit=depth_limit,
        note="Khong tim thay loi giai trong gioi han do sau hien tai.",
    )


def solve_greedy(start, goal, size, heuristic_name="manhattan", node_limit=200000, trace_limit=220, tree_limit=120):
    """
    Giải 8-puzzle bằng Greedy Best-First Search.

    Nguyên lý:
    - Mỗi trạng thái được đánh giá bằng h(n), tức khoảng cách ước lượng từ trạng thái hiện tại đến goal.
    - Luôn chọn trạng thái có h(n) nhỏ nhất để mở rộng trước.

    Công thức ưu tiên:
    - priority = h(n)

    Đặc điểm:
    - Thường chạy nhanh vì luôn lao về phía trạng thái có vẻ gần đích.
    - Không đảm bảo tìm lời giải ngắn nhất vì bỏ qua chi phí đã đi g(n).
    """
    started_at = time.time()
    heuristic_label = get_heuristic_label(heuristic_name)

    # Greedy chỉ dùng h(n), nên tính h cho trạng thái start để đưa vào hàng đợi ưu tiên.
    start_h = calculate_heuristic(start, goal, size, heuristic_name)

    counter = itertools.count()

    # frontier của Greedy có dạng: (h, depth, thứ_tự, state).
    # h càng nhỏ thì trạng thái càng được ưu tiên.
    frontier = [(start_h, 0, next(counter), start)]

    parents = {start: (None, None, 0)}

    # visited: trạng thái đã được đưa vào frontier.
    visited = {start}

    # closed: trạng thái đã được lấy ra và mở rộng.
    closed = set()

    trace_rows = [_trace_row(1, 0, "Start", start, size)]
    tree_nodes = [{
        "id": "G0",
        "parent": "",
        "text": f"Start | d=0 | h={format_heuristic_value(start_h)} | {format_state_inline(start, size)}",
    }]
    tree_ids = {start: "G0"}
    tree_counter = 1

    if start == goal:
        return _result(
            True,
            "Greedy",
            start,
            size,
            [],
            1,
            0,
            0,
            trace_rows,
            tree_nodes,
            started_at,
            note="Trang thai dau da la trang thai dich.",
            heuristic=heuristic_label,
        )

    step = 1
    expanded_count = 0
    max_depth = 0

    while frontier:
        # Lấy trạng thái có h(n) nhỏ nhất.
        current_h, current_depth, _, current = heapq.heappop(frontier)

        # Nếu đã mở rộng rồi thì không mở rộng lại.
        if current in closed:
            continue

        closed.add(current)
        expanded_count += 1

        if current == goal:
            path = _path_from_parents(parents, current)
            return _result(
                True,
                "Greedy",
                start,
                size,
                path,
                len(visited),
                expanded_count,
                max_depth,
                trace_rows,
                tree_nodes,
                started_at,
                heuristic=heuristic_label,
            )

        for move, neighbor in generate_neighbors(current, size):
            if neighbor in visited:
                continue

            child_depth = current_depth + 1

            # Greedy đánh giá neighbor chỉ bằng h(n).
            child_h = calculate_heuristic(neighbor, goal, size, heuristic_name)

            visited.add(neighbor)
            parents[neighbor] = (current, move, child_depth)
            max_depth = max(max_depth, child_depth)

            # Đưa neighbor vào heap theo độ ưu tiên h nhỏ nhất.
            heapq.heappush(frontier, (child_h, child_depth, next(counter), neighbor))

            step += 1
            if len(trace_rows) < trace_limit:
                trace_rows.append(_trace_row(step, child_depth, MOVE_LABELS[move], neighbor, size))

            if len(tree_nodes) < tree_limit:
                parent_id = tree_ids.get(current, "")
                node_id = f"G{tree_counter}"
                tree_counter += 1
                tree_ids[neighbor] = node_id
                tree_nodes.append({
                    "id": node_id,
                    "parent": parent_id,
                    "text": f"{MOVE_LABELS[move]} | d={child_depth} | h={format_heuristic_value(child_h)} | {format_state_inline(neighbor, size)}",
                })

            if len(visited) >= node_limit:
                return _result(
                    False,
                    "Greedy",
                    start,
                    size,
                    [],
                    len(visited),
                    expanded_count,
                    max_depth,
                    trace_rows,
                    tree_nodes,
                    started_at,
                    note=f"Da dung vi vuot gioi han {node_limit} trang thai.",
                    heuristic=heuristic_label,
                )

    return _result(
        False,
        "Greedy",
        start,
        size,
        [],
        len(visited),
        expanded_count,
        max_depth,
        trace_rows,
        tree_nodes,
        started_at,
        note="Khong tim thay loi giai.",
        heuristic=heuristic_label,
    )


def solve_astar(start, goal, size, heuristic_name="manhattan", node_limit=200000, trace_limit=260, tree_limit=140):
    """
    Giải 8-puzzle bằng A*.

    Nguyên lý:
    - g(n): chi phí thật đã đi từ start đến trạng thái n.
    - h(n): chi phí ước lượng còn lại từ n đến goal.
    - f(n) = g(n) + h(n): tổng chi phí dự đoán của đường đi qua n.
    - Luôn mở rộng trạng thái có f(n) nhỏ nhất.

    Đặc điểm:
    - Cân bằng giữa đường đã đi và độ gần đích.
    - Với heuristic phù hợp, A* thường tìm lời giải tối ưu hơn Greedy.
    """
    started_at = time.time()
    heuristic_label = get_heuristic_label(heuristic_name)
    start_h = calculate_heuristic(start, goal, size, heuristic_name)

    counter = itertools.count()

    # frontier của A* có dạng: (f, h, g, thứ_tự, state).
    # Trong đó f = g + h; trạng thái có f nhỏ nhất được mở rộng trước.
    frontier = [(start_h, start_h, 0, next(counter), start)]

    parents = {start: (None, None, 0)}

    # best_g[state] lưu chi phí thật nhỏ nhất đã biết từ start đến state.
    best_g = {start: 0}

    trace_rows = [_trace_row(1, 0, "Start", start, size)]
    tree_nodes = [{
        "id": "A0",
        "parent": "",
        "text": f"Start | g=0 | h={format_heuristic_value(start_h)} | f={format_heuristic_value(start_h)} | {format_state_inline(start, size)}",
    }]
    tree_ids = {start: "A0"}
    tree_counter = 1

    if start == goal:
        return _result(
            True,
            "A*",
            start,
            size,
            [],
            1,
            0,
            0,
            trace_rows,
            tree_nodes,
            started_at,
            note="Trang thai dau da la trang thai dich.",
            heuristic=heuristic_label,
        )

    step = 1
    expanded_count = 0
    max_depth = 0

    while frontier:
        # Lấy trạng thái có f(n) = g(n) + h(n) nhỏ nhất.
        current_f, current_h, current_g, _, current = heapq.heappop(frontier)

        # Nếu bản ghi này cũ vì đã có đường khác đến current với g nhỏ hơn, bỏ qua.
        if current_g != best_g.get(current):
            continue

        expanded_count += 1

        if current == goal:
            path = _path_from_parents(parents, current)
            return _result(
                True,
                "A*",
                start,
                size,
                path,
                len(best_g),
                expanded_count,
                max_depth,
                trace_rows,
                tree_nodes,
                started_at,
                heuristic=heuristic_label,
            )

        for move, neighbor in generate_neighbors(current, size):
            # Với 8-puzzle, mỗi lần trượt ô được tính là 1 bước nên g tăng thêm 1.
            child_g = current_g + 1

            # Chỉ giữ đường đi tốt hơn, tức g nhỏ hơn đường đã biết trước đó.
            if child_g >= best_g.get(neighbor, float("inf")):
                continue

            child_depth = child_g

            # A* kết hợp chi phí đã đi g(n) và ước lượng còn lại h(n).
            child_h = calculate_heuristic(neighbor, goal, size, heuristic_name)
            child_f = child_g + child_h

            best_g[neighbor] = child_g
            parents[neighbor] = (current, move, child_depth)
            max_depth = max(max_depth, child_depth)

            # Đưa vào heap theo f nhỏ nhất; h và counter giúp phá hòa ổn định.
            heapq.heappush(frontier, (child_f, child_h, child_g, next(counter), neighbor))

            step += 1
            if len(trace_rows) < trace_limit:
                trace_rows.append(_trace_row(step, child_depth, MOVE_LABELS[move], neighbor, size))

            if len(tree_nodes) < tree_limit:
                parent_id = tree_ids.get(current, "")
                node_id = f"A{tree_counter}"
                tree_counter += 1
                tree_ids[neighbor] = node_id
                tree_nodes.append({
                    "id": node_id,
                    "parent": parent_id,
                    "text": f"{MOVE_LABELS[move]} | g={child_g} | h={format_heuristic_value(child_h)} | f={format_heuristic_value(child_f)} | {format_state_inline(neighbor, size)}",
                })

            if len(best_g) >= node_limit:
                return _result(
                    False,
                    "A*",
                    start,
                    size,
                    [],
                    len(best_g),
                    expanded_count,
                    max_depth,
                    trace_rows,
                    tree_nodes,
                    started_at,
                    note=f"Da dung vi vuot gioi han {node_limit} trang thai.",
                    heuristic=heuristic_label,
                )

    return _result(
        False,
        "A*",
        start,
        size,
        [],
        len(best_g),
        expanded_count,
        max_depth,
        trace_rows,
        tree_nodes,
        started_at,
        note="Khong tim thay loi giai.",
        heuristic=heuristic_label,
    )


def solve_with_algorithm(algorithm_name, start, goal, size, depth_limit=25, heuristic_name="manhattan"):
    """
    Hàm điều phối thuật toán theo lựa chọn từ giao diện.

    Giao diện chỉ cần gọi hàm này và truyền vào tên thuật toán đang chọn.
    Hàm sẽ tự chuyển đến:
    - solve_bfs
    - solve_dfs
    - solve_ucs
    - solve_greedy
    - solve_astar

    Tham số heuristic_name chỉ có tác dụng với Greedy và A*.
    """
    # Chuẩn hóa tên thuật toán để chấp nhận cả chữ thường/chữ hoa từ UI.
    algorithm_key = algorithm_name.strip().upper()

    if algorithm_key == "BFS":
        return solve_bfs(start, goal, size)

    if algorithm_key == "UCS":
        return solve_ucs(start, goal, size)

    if algorithm_key == "DFS":
        return solve_dfs(start, goal, size, depth_limit=depth_limit)

    # Chấp nhận nhiều cách viết để tránh lỗi nếu UI đổi tên hiển thị.
    if algorithm_key in {"GREEDY", "GREEDY BEST-FIRST SEARCH", "GBFS"}:
        return solve_greedy(start, goal, size, heuristic_name=heuristic_name)

    if algorithm_key in {"A*", "ASTAR", "A STAR"}:
        return solve_astar(start, goal, size, heuristic_name=heuristic_name)

    # Nếu tên thuật toán không thuộc các trường hợp trên thì báo lỗi rõ ràng.
    raise ValueError(f"Thuat toan khong duoc ho tro: {algorithm_name}")

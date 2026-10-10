import random

class Bot:
    """
    GreedyBot: Luôn ưu tiên di chuyển các quân cờ về phía ô đích của đối phương.
    Đỏ (RED) luôn muốn tiến về ô (8, 8).
    Xanh (BLUE) luôn muốn tiến về ô (0, 0).
    """
    def get_move(self, state_dict: dict) -> dict:
        board = state_dict["board"]
        size = len(board)
        
        team_name = state_dict.get("team", "RED")
        team_vals = [1, 2, 3] if team_name == "RED" else [4, 5, 6]
        
        # Tọa độ đích đến (Goal)
        target_r, target_c = (size - 1, size - 1) if team_name == "RED" else (0, 0)
        
        my_pieces = []
        for r in range(size):
            for c in range(size):
                if board[r][c] in team_vals:
                    my_pieces.append((r, c))
                    
        valid_moves = []
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]
        
        for r, c in my_pieces:
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < size and 0 <= nc < size:
                    target = board[nr][nc]
                    if target not in team_vals: # Không giẫm lên quân mình
                        # Không đi vào ô nhà mình
                        if team_name == "RED" and nr == 0 and nc == 0: continue
                        if team_name == "BLUE" and nr == size - 1 and nc == size - 1: continue
                        
                        # Tính khoảng cách Manhattan (hoặc Chebyshev) tới mục tiêu
                        dist_old = max(abs(r - target_r), abs(c - target_c))
                        dist_new = max(abs(nr - target_r), abs(nc - target_c))
                        
                        valid_moves.append({
                            "move": {"from": [r, c], "to": [nr, nc]},
                            "score": dist_old - dist_new # Điểm dương nghĩa là tiến gần hơn
                        })
                        
        if not valid_moves:
            raise Exception("No valid moves available")
            
        # Lọc ra những nước đi có điểm cao nhất (tiến gần mục tiêu nhất)
        max_score = max(m["score"] for m in valid_moves)
        best_moves = [m["move"] for m in valid_moves if m["score"] == max_score]
        
        # Chọn ngẫu nhiên giữa các nước đi tốt nhất
        return random.choice(best_moves)

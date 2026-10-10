import random
import sys
import os

# Cho phép import từ thư mục api (khi sinh viên test ở máy cá nhân)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.bot import BaseBot
from api.game_state import GameState
from api.move import Move

class Bot(BaseBot):
    """
    Một ví dụ minh họa cách sử dụng các class hỗ trợ từ thư mục `api/`
    để code gọn gàng theo hướng đối tượng (OOP).
    """
    def get_move(self, state_dict: dict) -> dict:
        # 1. Parse JSON dictionary sang Object GameState
        state = GameState(state_dict)
        
        # 2. Lấy danh sách quân của mình
        my_pieces = state.get_my_pieces()
        
        valid_moves = []
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]
        
        for r, c in my_pieces:
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < state.size and 0 <= nc < state.size:
                    # Kiểm tra giẫm quân đồng minh
                    if (nr, nc) not in my_pieces:
                        # Kiểm tra cấm giẫm vào nhà mình
                        if state.team == "RED" and nr == 0 and nc == 0: continue
                        if state.team == "BLUE" and nr == state.size - 1 and nc == state.size - 1: continue
                        
                        valid_moves.append(Move((r, c), (nr, nc)))
        
        if not valid_moves:
            raise Exception("Hết đường đi!")
            
        # 3. Chọn random 1 Move Object và trả về dưới dạng Dict
        chosen_move = random.choice(valid_moves)
        return chosen_move.to_dict()

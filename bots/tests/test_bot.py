import importlib.util
import os
import sys


def _load_bot_class():
    examples_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'examples'))
    module_path = os.path.join(examples_dir, 'greedy_bot.py')

    if not os.path.exists(module_path):
        raise FileNotFoundError(f"Không tìm thấy file Bot tại: {module_path}")

    spec = importlib.util.spec_from_file_location('greedy_bot', module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Không thể tải module từ: {module_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules['greedy_bot'] = module
    spec.loader.exec_module(module)
    return module.Bot


def run_test():
    try:
        Bot = _load_bot_class()
        bot = Bot()
    except Exception as e:
        print("❌ Lỗi khởi tạo Bot:", e)
        return
        
    print("✅ Khởi tạo Bot thành công.")
    
    # State giả lập cho test
    dummy_state = {
        "turn": 1,
        "team": "RED",
        "board": [[0] * 9 for _ in range(9)]
    }
    dummy_state["board"][0][1] = 1 # Đặt 1 quân RED ROCK
    
    print("\nTruyền vào State giả lập:")
    print(dummy_state)
    
    try:
        move = bot.get_move(dummy_state)
        print("\n✅ Bot trả về Move thành công:")
        print(move)
        
        if "from" in move and "to" in move:
            print("Cấu trúc JSON đầu ra hợp lệ!")
        else:
            print("❌ Thiếu 'from' hoặc 'to' trong kết quả.")
    except Exception as e:
        print("\n❌ Lỗi khi gọi get_move:", e)

if __name__ == "__main__":
    run_test()

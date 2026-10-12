import subprocess
import json
import time
from typing import Dict, Any, Optional, Tuple

class BotRunner:
    def __init__(self, bot_file_path: str, team_name: str, use_docker: bool = True):
        self.bot_file_path = bot_file_path
        self.team_name = team_name
        self.use_docker = use_docker
        self.process: Optional[subprocess.Popen] = None

    def start(self):
        """Khởi chạy tiến trình Bot"""
        if self.use_docker:
            # Lệnh chạy Docker Sandbox cô lập tài nguyên
            cmd = [
                "docker", "run", "-i", "--rm",
                "--network", "none",
                "--memory", "128m",
                "--cpus", "0.5",
                "-v", f"{self.bot_file_path}:/app/student_bot.py:ro",
                "uet_bot_sandbox:latest"
            ]
        else:
            # Chạy local trực tiếp (dùng cho debug/dev)
            cmd = ["python", "-u", self.bot_file_path]

        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

    def get_move(self, game_state: Dict[str, Any], timeout: float) -> Tuple[Optional[Dict[str, Any]], float, Optional[str]]:
        """Gửi Game State qua stdin và nhận Move từ stdout trong thời gian timeout"""
        if not self.process or self.process.poll() is not None:
            return None, 0.0, "PROCESS_CRASHED"

        start_time = time.time()
        try:
            # 1. Gửi trạng thái sang Bot dưới dạng 1 dòng JSON
            input_data = json.dumps(game_state) + "\n"
            self.process.stdin.write(input_data)
            self.process.stdin.flush()

            # 2. Chờ đọc nước đi từ Bot
            raw_output = self.process.stdout.readline()
            elapsed_time = time.time() - start_time

            if elapsed_time > timeout:
                return None, elapsed_time, "TIMEOUT"

            if not raw_output:
                return None, elapsed_time, "EMPTY_RESPONSE"

            move = json.loads(raw_output.strip())
            return move, elapsed_time, None

        except json.JSONDecodeError:
            return None, time.time() - start_time, "INVALID_JSON_FORMAT"
        except Exception as e:
            return None, time.time() - start_time, f"EXCEPTION: {str(e)}"

    def stop(self):
        """Dọn dẹp và dừng tiến trình"""
        if self.process:
            try:
                self.process.kill()
                self.process.wait(timeout=1.0)
            except Exception:
                pass
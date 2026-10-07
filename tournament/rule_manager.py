# tournament/rule_manager.py
import json
import os
from typing import Any, Dict


class RuleManager:
    """Quản lý và nạp RuleSet cho từng vòng đấu từ folder configs/[cite: 7]."""

    def __init__(self, config_dir: str = "configs"):
        self.config_dir = config_dir

    def get_stage_config(self, stage_name: str) -> Dict[str, Any]:
        """
        Nạp file JSON tương ứng (qualification, top32, top16, quarterfinal, semifinal, final)[cite: 7].
        Nếu chưa có file, tự động trả về cấu hình chuẩn cho vòng đấu đó[cite: 7].
        """
        file_path = os.path.join(self.config_dir, f"{stage_name}.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[RuleManager Warning] Lỗi đọc file {file_path}: {e}")

        # Cấu hình dự phòng chuẩn theo spec[cite: 7]
        default_configs = {
            "qualification": {
                "best_of": 1,
                "board_size": 9,
                "max_turns": 200,
                "move_time_limit": 1.0,
            },
            "top32": {
                "best_of": 3,
                "board_size": 9,
                "max_turns": 200,
                "move_time_limit": 1.0,
            },
            "top16": {
                "best_of": 3,
                "board_size": 9,
                "max_turns": 200,
                "move_time_limit": 1.0,
            },
            "quarterfinal": {
                "best_of": 5,
                "board_size": 9,
                "max_turns": 200,
                "move_time_limit": 1.0,
            },
            "semifinal": {
                "best_of": 5,
                "board_size": 9,
                "max_turns": 200,
                "move_time_limit": 1.0,
            },
            "final": {
                "best_of": 7,
                "board_size": 9,
                "max_turns": 200,
                "move_time_limit": 1.0,
            },
        }
        return default_configs.get(
            stage_name,
            {"best_of": 1, "board_size": 9, "max_turns": 200, "move_time_limit": 1.0},
        )
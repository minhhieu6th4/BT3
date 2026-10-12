import importlib.util
import os
from types import SimpleNamespace

from game.game_engine import GameEngine
from game.piece import Team
from game.rule_set import RuleSet


class MatchRunner:
    """Chạy một trận đấu giữa 2 bot và trả về kết quả tương thích với TournamentEngine."""

    def __init__(self, bot1_path: str, bot2_path: str, max_turns: int = 200, move_timeout: float = 2.0):
        self.bot1_path = self._normalize_path(bot1_path)
        self.bot2_path = self._normalize_path(bot2_path)
        self.max_turns = max_turns
        self.move_timeout = move_timeout

    @staticmethod
    def _normalize_path(path: str) -> str:
        if not path:
            raise ValueError("Đường dẫn bot không được để trống")
        if os.path.isabs(path):
            return path
        return os.path.abspath(path)

    @staticmethod
    def _load_bot_module(bot_path: str):
        if not os.path.exists(bot_path):
            raise FileNotFoundError(f"Không tìm thấy bot tại: {bot_path}")

        module_name = f"bot_{abs(hash(bot_path))}"
        spec = importlib.util.spec_from_file_location(module_name, bot_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Không thể nạp module từ: {bot_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        bot_cls = getattr(module, "Bot", None)
        if bot_cls is None:
            raise AttributeError(f"File bot '{bot_path}' không chứa class 'Bot'")

        return bot_cls()

    @staticmethod
    def _to_winner_id(winner_team):
        if winner_team is None:
            return None
        if winner_team == Team.RED:
            return 1
        if winner_team == Team.BLUE:
            return 2
        return None

    def run_match(self):
        """Chạy một ván đấu và trả về object có các thuộc tính: winner, reason, moves."""
        try:
            red_bot = self._load_bot_module(self.bot1_path)
        except Exception as exc:
            return SimpleNamespace(
                winner=2,
                winner_team="BLUE",
                reason=f"Bot RED lỗi khi khởi tạo: {exc}",
                moves=[],
            )

        try:
            blue_bot = self._load_bot_module(self.bot2_path)
        except Exception as exc:
            return SimpleNamespace(
                winner=1,
                winner_team="RED",
                reason=f"Bot BLUE lỗi khi khởi tạo: {exc}",
                moves=[],
            )

        rule_set = RuleSet.default()
        rule_set.max_turns = self.max_turns
        rule_set.move_time_limit = self.move_timeout

        engine = GameEngine(rule_set)
        try:
            result = engine.play(red_bot, blue_bot)
        except Exception as exc:
            return SimpleNamespace(
                winner=None,
                winner_team=None,
                reason=f"Exception khi chơi ván đấu: {exc}",
                moves=engine.state.move_log,
            )

        moves = list(getattr(engine.state, "move_log", []))
        winner_id = self._to_winner_id(getattr(result, "winner", None))
        return SimpleNamespace(
            winner=winner_id,
            winner_team=getattr(result.winner, "value", None),
            reason=getattr(result, "reason", "Game finished"),
            moves=moves,
            total_turns=getattr(engine.state, "turn", 0),
            result=result,
        )

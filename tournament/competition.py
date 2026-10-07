# tournament/competition.py
import math
from typing import Any, Dict, List, Optional

from .knockout import KnockoutManager
from .qualification import QualificationManager
from .ranking import RankingManager
from .rule_manager import RuleManager
from .seeding import SeedingManager

# Tích hợp với MatchRunner của Judge[cite: 7]
try:
    from judge.match_runner import MatchRunner
except ImportError:
    # Class Mock để test độc lập nếu chưa kết nối Judge
    import random

    class DummyResult:

        def __init__(self):
            self.winner = random.choice([1, 2, None])
            self.reason = "Kết quả giả lập Game Engine"
            self.moves = []

    class MatchRunner:

        def __init__(self, bot1_path: str, bot2_path: str, max_turns: int = 200):
            pass

        def run_match(self) -> DummyResult:
            return DummyResult()


class TournamentEngine:
    """Master Orchestrator điều hành 100 Đội qua toàn bộ các giai đoạn[cite: 7]."""

    def __init__(self, team_bot_paths: Dict[str, str], config_dir: str = "configs"):
        self.team_bot_paths = team_bot_paths
        self.rule_mgr = RuleManager(config_dir)
        self.qual_mgr = QualificationManager()
        self.ranking_mgr = RankingManager()
        self.tournament_logs: List[Dict[str, Any]] = []

    def _execute_match_series(
        self, team1: str, team2: str, best_of: int, stage_name: str
    ) -> Dict[str, Any]:
        """
        Thực thi 1 Match gồm chuỗi nhiều Game (BO series)[cite: 7].
        Phân biệt rõ Match và Game[cite: 7]. Match kết thúc khi 1 đội chạm đủ số trận thắng target_wins[cite: 7].
        """
        target_wins = math.ceil(best_of / 2)
        team1_wins = 0
        team2_wins = 0
        games_played = []

        bot1_path = self.team_bot_paths[team1]
        bot2_path = self.team_bot_paths[team2]

        config = self.rule_mgr.get_stage_config(stage_name)
        max_turns = config.get("max_turns", 200)

        for game_idx in range(1, best_of + 1):
            runner = MatchRunner(bot1_path, bot2_path, max_turns=max_turns)
            game_result = runner.run_match()

            g_winner = game_result.winner
            if g_winner == 1:
                team1_wins += 1
            elif g_winner == 2:
                team2_wins += 1

            games_played.append(
                {
                    "game_num": game_idx,
                    "winner": g_winner,
                    "reason": getattr(game_result, "reason", "Normal finish"),
                    "moves": getattr(game_result, "moves", []),
                }
            )

            # Dừng chuỗi đấu ngay khi có đội chạm mốc chiến thắng[cite: 7]
            if team1_wins >= target_wins or team2_wins >= target_wins:
                break

        # Xác định đội chiến thắng của Match
        if team1_wins > team2_wins:
            match_winner_id = 1
            winner_team = team1
        elif team2_wins > team1_wins:
            match_winner_id = 2
            winner_team = team2
        else:
            match_winner_id = None
            winner_team = None

        match_log = {
            "stage": stage_name,
            "team1": team1,
            "team2": team2,
            "best_of": best_of,
            "score": f"{team1_wins}-{team2_wins}",
            "winner_id": match_winner_id,
            "winner_team": winner_team,
            "games": games_played,
        }
        self.tournament_logs.append(match_log)
        return match_log

    def run_qualification_stage(
        self, all_teams: List[str]
    ) -> Dict[str, Any]:
        """Giai đoạn Vòng Bảng: 10 Bảng x 10 Đội (450 Matches BO1)[cite: 7]."""
        groups = self.qual_mgr.setup_qualification(all_teams)
        print(
            f"\n======== KHỞI CHẠY VÒNG BẢNG ({self.qual_mgr.get_total_matches_count()} TRẬN BO1) ========"
        )

        for group_name, group in groups.items():
            matchups = group.get_matchups()
            print(f"--- Đang thi đấu {group_name} ({len(matchups)} trận) ---")
            for team1, team2 in matchups:
                match_res = self._execute_match_series(
                    team1, team2, best_of=1, stage_name="qualification"
                )

                group.record_match(match_res)
                self.ranking_mgr.record_match_result(
                    team1, team2, match_res["winner_id"]
                )

        return groups

    def run_knockout_stage(self, top_32_teams: List[str]) -> str:
        """Giai đoạn Knockout: Top 32 -> 16 (BO3) -> Tứ kết (BO5) -> Bán kết (BO5) -> Chung kết (BO7)[cite: 7]."""
        current_teams = top_32_teams

        while len(current_teams) > 1:
            num_teams = len(current_teams)
            best_of = KnockoutManager.get_best_of_format(num_teams)
            stage_name_map = {
                32: "top32",
                16: "top16",
                8: "quarterfinal",
                4: "semifinal",
                2: "final",
            }
            stage_key = stage_name_map.get(num_teams, "top32")

            print(
                f"\n======== VÒNG KNOCKOUT {num_teams} ĐỘI (Thể thức BO{best_of}) ========"
            )

            seeded_teams = SeedingManager.generate_seeds(
                current_teams, self.ranking_mgr
            )
            pairings = KnockoutManager.create_pairings(seeded_teams)
            next_round_winners = []

            for team1, team2 in pairings:
                match_res = self._execute_match_series(
                    team1, team2, best_of=best_of, stage_name=stage_key
                )

                # Nếu hòa trong Knockout, ưu tiên đội hạt giống cao hơn (team1)
                winner = (
                    match_res["winner_team"]
                    if match_res["winner_team"]
                    else team1
                )
                next_round_winners.append(winner)

            current_teams = next_round_winners

        champion = current_teams[0]
        print(
            f"\n======================================================="
        )
        print(f" CHAMPION / NHÀ VÔ ĐỊCH UET ALGORITHM BATTLE: {champion}")
        print(
            f"======================================================="
        )
        return champion
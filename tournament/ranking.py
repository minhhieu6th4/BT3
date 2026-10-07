from functools import cmp_to_key
from typing import Any, Dict, List, Optional


class RankingManager:
    """
    Quản lý điểm số và xếp hạng vòng bảng[cite: 7].
    Tiêu chí tie-break theo đúng yêu cầu[cite: 7]:
    1. Điểm số (Thắng = 3đ, Hòa = 1đ, Thua = 0đ)[cite: 7]
    2. Đối đầu trực tiếp (Head-to-head)[cite: 7]
    3. Tổng số trận thắng[cite: 7]
    """

    def __init__(self):
        self.stats: Dict[str, Dict[str, Any]] = {}
        self.head_to_head: Dict[str, Dict[str, Optional[int]]] = {}

    def register_teams(self, teams: List[str]) -> None:
        for t in teams:
            if t not in self.stats:
                self.stats[t] = {
                    "points": 0,
                    "wins": 0,
                    "draws": 0,
                    "losses": 0,
                    "matches_played": 0,
                }
            if t not in self.head_to_head:
                self.head_to_head[t] = {}

    def record_match_result(
        self, team1: str, team2: str, winner: Optional[int]
    ) -> None:
        self.register_teams([team1, team2])
        self.stats[team1]["matches_played"] += 1
        self.stats[team2]["matches_played"] += 1

        # Lưu đối đầu: 1 (team1 thắng), 2 (team2 thắng), None (hòa)
        self.head_to_head[team1][team2] = winner
        self.head_to_head[team2][team1] = (
            1 if winner == 2 else (2 if winner == 1 else None)
        )

        if winner == 1:
            self.stats[team1]["points"] += 3
            self.stats[team1]["wins"] += 1
            self.stats[team2]["losses"] += 1
        elif winner == 2:
            self.stats[team2]["points"] += 3
            self.stats[team2]["wins"] += 1
            self.stats[team1]["losses"] += 1
        else:  # Hòa
            self.stats[team1]["points"] += 1
            self.stats[team2]["points"] += 1
            self.stats[team1]["draws"] += 1
            self.stats[team2]["draws"] += 1

    def _compare_teams(
        self, team_a: Dict[str, Any], team_b: Dict[str, Any]
    ) -> int:
        # 1. So Điểm
        if team_a["points"] != team_b["points"]:
            return 1 if team_a["points"] > team_b["points"] else -1

        # 2. So Đối đầu trực tiếp
        h2h_winner = self.head_to_head.get(team_a["team_id"], {}).get(
            team_b["team_id"]
        )
        if h2h_winner == 1:
            return 1
        if h2h_winner == 2:
            return -1

        # 3. So Tổng số trận thắng
        if team_a["wins"] != team_b["wins"]:
            return 1 if team_a["wins"] > team_b["wins"] else -1

        return 0

    def get_ranked_list(
        self, filter_teams: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        target_teams = (
            filter_teams if filter_teams is not None else list(self.stats.keys())
        )
        filtered_stats = [
            {"team_id": t, **self.stats[t]}
            for t in target_teams
            if t in self.stats
        ]

        return sorted(
            filtered_stats, key=cmp_to_key(self._compare_teams), reverse=True
        )

    def select_top_32(self, groups: Dict[str, Any]) -> List[str]:
        """
        Chọn Top 32 theo đúng quy tắc[cite: 7]:
        - Top 3 của 10 bảng x 10 = 30 đội[cite: 7].
        - 2 đội hạng 4 có thành tích xuất sắc nhất = 2 đội[cite: 7].
        """
        top_32 = []
        fourth_place_candidates = []

        for _, group in groups.items():
            standings = self.get_ranked_list(group.teams)
            for i in range(min(3, len(standings))):
                top_32.append(standings[i]["team_id"])
            if len(standings) >= 4:
                fourth_place_candidates.append(standings[3])

        # Sắp xếp các đội hạng 4 dựa trên tổng điểm và số trận thắng[cite: 7]
        fourth_place_sorted = sorted(
            fourth_place_candidates,
            key=lambda x: (x["points"], x["wins"]),
            reverse=True,
        )

        for i in range(min(2, len(fourth_place_sorted))):
            top_32.append(fourth_place_sorted[i]["team_id"])

        return top_32
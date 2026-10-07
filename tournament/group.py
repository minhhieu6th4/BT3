from typing import List, Dict, Tuple, Any
from tournament.ranking import RankingManager

class Group:
    def __init__(self, name: str, teams: List[str] = None):
        """
        Khởi tạo một bảng đấu.
        :param name: Tên bảng đấu (ví dụ: "Group_A", "Group_B")
        :param teams: Danh sách ID các đội trong bảng
        """
        self.name = name
        self.teams = teams if teams else []
        self.ranking_mgr = RankingManager()
        self.ranking_mgr.register_teams(self.teams)
        self.matches = []  # Lưu lịch sử các trận đấu trong bảng

    def add_team(self, team_id: str):
        """Thêm 1 đội vào bảng đấu."""
        if team_id not in self.teams:
            self.teams.append(team_id)
            self.ranking_mgr.register_teams([team_id])

    def get_matchups(self) -> List[Tuple[str, str]]:
        """Tạo danh sách các cặp đấu vòng tròn 1 lượt (Round Robin) trong bảng này."""
        matchups = []
        n = len(self.teams)
        for i in range(n):
            for j in range(i + 1, n):
                matchups.append((self.teams[i], self.teams[j]))
        return matchups

    def record_match_result(self, team1: str, team2: str, winner: int, reason: str = ""):
        """Lưu kết quả trận đấu và cập nhật bảng xếp hạng nội bộ của bảng."""
        self.ranking_mgr.record_match(team1, team2, winner)
        self.matches.append({
            "group": self.name,
            "team1": team1,
            "team2": team2,
            "winner": winner,
            "reason": reason
        })

    def get_standings(self) -> List[Dict[str, Any]]:
        """Lấy bảng xếp hạng hiện tại của bảng đấu này (đã sắp xếp theo điểm/số trận thắng)."""
        return self.ranking_mgr.get_ranked_list(self.teams)

    def get_top_teams(self, count: int = 3) -> List[str]:
        """Lấy danh sách N đội đứng đầu bảng."""
        standings = self.get_standings()
        return [team_info["team_id"] for team_info in standings[:count]]
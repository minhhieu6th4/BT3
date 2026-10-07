from typing import Any, Dict, List, Tuple


class Group:
    """Đại diện cho 1 Bảng đấu (Group A -> Group J) gồm 10 đội[cite: 7]."""

    def __init__(self, name: str, teams: List[str] = None):
        self.name = name
        self.teams: List[str] = teams if teams is not None else []
        self.matches: List[Dict[str, Any]] = []

    def add_team(self, team_id: str) -> None:
        if team_id not in self.teams:
            self.teams.append(team_id)

    def get_matchups(self) -> List[Tuple[str, str]]:
        """Tạo danh sách 45 cặp đấu vòng tròn 1 lượt (C(10, 2) = 45)[cite: 7]."""
        matchups = []
        n = len(self.teams)
        for i in range(n):
            for j in range(i + 1, n):
                matchups.append((self.teams[i], self.teams[j]))
        return matchups

    def record_match(self, match_data: Dict[str, Any]) -> None:
        """Lưu vết thông tin Match đã diễn ra trong bảng[cite: 7]."""
        self.matches.append(match_data)
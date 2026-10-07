from typing import List, Dict, Any

class RankingManager:
    def __init__(self):
        # Cấu trúc: { team_id: {"points": 0, "wins": 0, "draws": 0, "losses": 0, "matches_played": 0} }
        self.stats: Dict[str, Dict[str, int]] = {}

    def register_teams(self, teams: List[str]):
        """Đăng ký danh sách các đội vào hệ thống tính điểm."""
        for team in teams:
            if team not in self.stats:
                self.stats[team] = {
                    "points": 0,
                    "wins": 0,
                    "draws": 0,
                    "losses": 0,
                    "matches_played": 0
                }

    def record_match(self, team1: str, team2: str, winner: int):
        """
        Cập nhật kết quả trận đấu:
        winner = 1 (team1 thắng), winner = 2 (team2 thắng), winner = None (hòa)
        Thắng = 3đ, Hòa = 1đ, Thua = 0đ
        """
        self.register_teams([team1, team2])
        self.stats[team1]["matches_played"] += 1
        self.stats[team2]["matches_played"] += 1

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

    def get_ranked_list(self, filter_teams: List[str] = None) -> List[Dict[str, Any]]:
        """Sắp xếp đội theo Điểm số -> Số trận thắng."""
        target_teams = filter_teams if filter_teams else list(self.stats.keys())
        filtered_stats = [
            {"team_id": team, **self.stats[team]}
            for team in target_teams if team in self.stats
        ]
        
        # Sắp xếp ưu tiên: Điểm (points) cao nhất -> Số trận thắng (wins) nhiều nhất
        ranked = sorted(
            filtered_stats,
            key=lambda x: (x["points"], x["wins"]),
            reverse=True
        )
        return ranked

    def select_top_32(self, all_groups: Dict[str, List[str]]) -> List[str]:
        """
        Luật chọn Top 32:
        - Lấy Top 3 đội đứng đầu mỗi bảng x 10 bảng = 30 đội
        - Lấy 2 đội xếp thứ 4 có điểm số tốt nhất toàn bộ giải = 2 đội
        => Tổng cộng 32 đội
        """
        top_32 = []
        fourth_place_candidates = []

        for group_name, group_teams in all_groups.items():
            group_ranking = self.get_ranked_list(group_teams)
            
            # Lấy 3 đội đầu bảng
            for i in range(min(3, len(group_ranking))):
                top_32.append(group_ranking[i]["team_id"])
                
            # Đội xếp thứ 4 làm ứng viên Vé vớt (Wildcard)
            if len(group_ranking) >= 4:
                fourth_place_candidates.append(group_ranking[3])

        # Sắp xếp các đội hạng 4 để lấy 2 đội tốt nhất
        fourth_place_sorted = sorted(
            fourth_place_candidates,
            key=lambda x: (x["points"], x["wins"]),
            reverse=True
        )

        for i in range(min(2, len(fourth_place_sorted))):
            top_32.append(fourth_place_sorted[i]["team_id"])

        return top_32
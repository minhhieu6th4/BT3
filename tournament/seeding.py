from typing import List
from .ranking import RankingManager


class SeedingManager:
    """Xếp hạt giống từ 1 đến 32 cho Top 32 đội bước vào vòng Knockout[cite: 7]."""

    @staticmethod
    def generate_seeds(
        top_32_teams: List[str], ranking_mgr: RankingManager
    ) -> List[str]:
        ranked = ranking_mgr.get_ranked_list(top_32_teams)
        return [item["team_id"] for item in ranked]
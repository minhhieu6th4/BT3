from typing import List, Dict, Any

class SeedingManager:
    @staticmethod
    def generate_seeds(top_32_teams: List[str], ranking_manager) -> List[str]:
        """Đánh thứ tự hạt giống từ Seed 1 đến Seed 32."""
        ranked_32 = ranking_manager.get_ranked_list(top_32_teams)
        seed_list = [item["team_id"] for item in ranked_32]
        return seed_list
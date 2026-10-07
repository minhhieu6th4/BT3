from typing import List, Tuple

class KnockoutManager:
    @staticmethod
    def create_round_pairings(seeded_teams: List[str]) -> List[Tuple[str, str]]:
        """
        Ghép cặp thi đấu theo quy tắc đối xứng hạt giống:
        Ví dụ vòng 32 đội: Seed 1 vs Seed 32, Seed 2 vs Seed 31...
        """
        pairings = []
        num_teams = len(seeded_teams)
        for i in range(num_teams // 2):
            team1 = seeded_teams[i]
            team2 = seeded_teams[num_teams - 1 - i]
            pairings.append((team1, team2))
        return pairings
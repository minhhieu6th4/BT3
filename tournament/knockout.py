from typing import List, Tuple


class KnockoutManager:
    """Quản lý phân cặp ghép đấu hạt giống và thể thức Best-Of cho Knockout[cite: 7]."""

    # Cấu hình Best-Of theo từng vòng đấu[cite: 7]
    STAGE_BEST_OF = {
        32: 3,  # Round of 32: BO3[cite: 7]
        16: 3,  # Round of 16: BO3[cite: 7]
        8: 5,  # Quarterfinal: BO5[cite: 7]
        4: 5,  # Semifinal: BO5[cite: 7]
        2: 7,  # Final: BO7[cite: 7]
    }

    @staticmethod
    def create_pairings(seeded_teams: List[str]) -> List[Tuple[str, str]]:
        """Ghép cặp theo nguyên tắc: Hạt giống cao nhất gặp hạt giống thấp nhất (1 vs 32, 2 vs 31...)[cite: 7]."""
        pairings = []
        n = len(seeded_teams)
        for i in range(n // 2):
            pairings.append((seeded_teams[i], seeded_teams[n - 1 - i]))
        return pairings

    @classmethod
    def get_best_of_format(cls, num_teams_in_round: int) -> int:
        return cls.STAGE_BEST_OF.get(num_teams_in_round, 3)
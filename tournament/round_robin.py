from typing import Dict, List
from .group import Group


class RoundRobinManager:
    """Quản lý việc chia 100 đội thành 10 bảng đấu x 10 đội[cite: 7]."""

    @staticmethod
    def divide_into_groups(
        teams: List[str], num_groups: int = 10
    ) -> Dict[str, Group]:
        groups: Dict[str, Group] = {}
        teams_per_group = len(teams) // num_groups

        for i in range(num_groups):
            group_letter = chr(65 + i)  # 'A', 'B', ..., 'J'[cite: 7]
            group_name = f"Group_{group_letter}"
            start_idx = i * teams_per_group
            end_idx = (
                start_idx + teams_per_group
                if i < num_groups - 1
                else len(teams)
            )

            group_obj = Group(name=group_name, teams=teams[start_idx:end_idx])
            groups[group_name] = group_obj

        return groups
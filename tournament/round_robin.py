from typing import List, Dict
from tournament.group import Group

class RoundRobinManager:
    @staticmethod
    def divide_into_groups(teams: List[str], num_groups: int = 10) -> Dict[str, Group]:
        """
        Chia danh sách các đội thành các đối tượng Group.
        :param teams: Danh sách ID các đội thi đấu (ví dụ 100 đội)
        :param num_groups: Số lượng bảng đấu (Mặc định: 10 bảng)
        :return: Dictionary dạng {"Group_A": Group, "Group_B": Group, ...}
        """
        groups: Dict[str, Group] = {}
        teams_per_group = len(teams) // num_groups

        for i in range(num_groups):
            group_letter = chr(65 + i)  # 'A', 'B', 'C', ..., 'J'
            group_name = f"Group_{group_letter}"
            
            start_idx = i * teams_per_group
            # Bảng cuối cùng sẽ nhận toàn bộ số đội còn dư (nếu có)
            end_idx = start_idx + teams_per_group if i < num_groups - 1 else len(teams)
            
            group_teams = teams[start_idx:end_idx]
            
            # Khởi tạo đối tượng Group
            group_obj = Group(name=group_name, teams=group_teams)
            groups[group_name] = group_obj

        return groups
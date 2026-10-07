# tournament/competition.py
from typing import Dict, List, Any
from tournament.group import Group
from tournament.round_robin import RoundRobinManager
from tournament.ranking import RankingManager
from tournament.seeding import SeedingManager
from tournament.knockout import KnockoutManager
from judge.match_runner import MatchRunner  # Tích hợp với TV2

class TournamentEngine:
    def __init__(self, team_bot_paths: Dict[str, str]):
        self.team_bot_paths = team_bot_paths
        self.global_ranking_mgr = RankingManager()
        self.groups: Dict[str, Group] = {}
        self.tournament_logs: List[Dict[str, Any]] = []

    def run_group_stage(self, teams: List[str]) -> Dict[str, Group]:
        self.groups = RoundRobinManager.divide_into_groups(teams, num_groups=10)
        
        for group_name, group in self.groups.items():
            matchups = group.get_matchups()
            print(f"--- Đang chạy Vòng bảng {group_name} ({len(matchups)} trận đấu) ---")
            
            for team1, team2 in matchups:
                bot1_path = self.team_bot_paths[team1]
                bot2_path = self.team_bot_paths[team2]

                runner = MatchRunner(bot1_path, bot2_path, max_turns=100)
                result = runner.run_match()

                group.record_match_result(team1, team2, result.winner, result.reason)
                self.global_ranking_mgr.record_match(team1, team2, result.winner)

                self.tournament_logs.append({
                    "stage": "GROUP_STAGE",
                    "group": group_name,
                    "team1": team1,
                    "team2": team2,
                    "winner": result.winner,
                    "reason": result.reason
                })

        return self.groups

    def select_top_32(self) -> List[str]:  # <-- Đã sửa (self)
        top_32 = []
        fourth_place_candidates = []

        for group_name, group in self.groups.items():
            standings = group.get_standings()
            
            for i in range(min(3, len(standings))):
                top_32.append(standings[i]["team_id"])
                
            if len(standings) >= 4:
                fourth_place_candidates.append(standings[3])

        fourth_place_sorted = sorted(
            fourth_place_candidates,
            key=lambda x: (x["points"], x["wins"]),
            reverse=True
        )

        for i in range(min(2, len(fourth_place_sorted))):
            top_32.append(fourth_place_sorted[i]["team_id"])

        return top_32

    def run_knockout_stage(self, qualified_teams: List[str]) -> str:
        current_round_teams = qualified_teams
        round_names = {
            32: "Top 32",
            16: "Top 16",
            8: "Tứ Kết (Top 8)",
            4: "Bán Kết (Top 4)",
            2: "Chung Kết (Final)"
        }

        while len(current_round_teams) > 1:
            num_teams = len(current_round_teams)
            round_title = round_names.get(num_teams, f"Vòng {num_teams} đội")
            print(f"\n======== ĐANG KHỞI CHẠY {round_title.upper()} ========")

            seeded_teams = SeedingManager.generate_seeds(current_round_teams, self.global_ranking_mgr)
            pairings = KnockoutManager.create_round_pairings(seeded_teams)
            next_round_winners = []

            for team1, team2 in pairings:
                bot1_path = self.team_bot_paths[team1]
                bot2_path = self.team_bot_paths[team2]

                runner = MatchRunner(bot1_path, bot2_path, max_turns=200)
                result = runner.run_match()

                if result.winner == 1:
                    winner_team = team1
                elif result.winner == 2:
                    winner_team = team2
                else:
                    winner_team = team1

                next_round_winners.append(winner_team)

                self.tournament_logs.append({
                    "stage": round_title,
                    "team1": team1,
                    "team2": team2,
                    "winner": winner_team,
                    "reason": result.reason
                })

            current_round_teams = next_round_winners

        champion = current_round_teams[0]
        print(f"\n==========================================")
        print(f" WINNER / ĐỘI VÔ ĐỊCH GIẢI ĐẤU: {champion}")
        print(f"==========================================")
        return champion
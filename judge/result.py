from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional

@dataclass
class MoveLog:
    turn: int
    team: str           # "RED" hoặc "BLUE"
    move: Dict[str, Any] # {"from": [r1, c1], "to": [r2, c2]}
    execution_time: float

@dataclass
class MatchResult:
    winner: str         # "RED", "BLUE", hoặc "DRAW"
    reason: str         # "REACH_GOAL", "TIMEOUT", "INVALID_MOVE", "CRASH", "MAX_TURNS"
    total_turns: int
    match_log: List[Dict[str, Any]]

    def to_json(self) -> Dict[str, Any]:
        return {
            "winner": self.winner,
            "reason": self.reason,
            "total_turns": self.total_turns,
            "match_log": self.match_log
        }


__all__ = ["MoveLog", "MatchResult"]
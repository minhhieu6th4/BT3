from .board import Board
from .piece import Team
from .rule_set import RuleSet

class GameState:
    def __init__(self, rule_set: RuleSet):
        self.turn = 1
        self.current_team = Team.RED
        self.board = Board(size=rule_set.board_size)
        self.rule_set = rule_set
        self.move_log = []

    def to_dict(self):
        """
        Export state as JSON for Bot API.
        Piece mapping:
        0 = Empty
        1 = RED ROCK, 2 = RED PAPER, 3 = RED SCISSORS
        4 = BLUE ROCK, 5 = BLUE PAPER, 6 = BLUE SCISSORS
        """
        board_repr = []
        for r in range(self.board.size):
            row_repr = []
            for c in range(self.board.size):
                piece = self.board.grid[r][c]
                if piece is None:
                    row_repr.append(0)
                else:
                    val = 1 if piece.piece_type.name == "ROCK" else (2 if piece.piece_type.name == "PAPER" else 3)
                    if piece.team == Team.BLUE:
                        val += 3
                    row_repr.append(val)
            board_repr.append(row_repr)

        return {
            "turn": self.turn,
            "team": self.current_team.value,
            "board": board_repr
        }

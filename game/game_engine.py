from .game_state import GameState
from .move import Move
from .piece import Piece, Team, PieceType
from .game_result import GameResult, ResultType
from .rule_set import RuleSet

class GameEngine:
    def __init__(self, rule_set: RuleSet):
        self.rule_set = rule_set
        self.state = GameState(rule_set)
        self._initialize_board()

    def _initialize_board(self):
        # A simple initial setup for testing.
        # Can be refined to match exact tournament rules later.
        size = self.rule_set.board_size
        
        # Red pieces
        self.state.board.set_piece((0, 1), Piece(Team.RED, PieceType.ROCK))
        self.state.board.set_piece((1, 0), Piece(Team.RED, PieceType.PAPER))
        self.state.board.set_piece((1, 1), Piece(Team.RED, PieceType.SCISSORS))
        
        # Blue pieces
        self.state.board.set_piece((size-1, size-2), Piece(Team.BLUE, PieceType.ROCK))
        self.state.board.set_piece((size-2, size-1), Piece(Team.BLUE, PieceType.PAPER))
        self.state.board.set_piece((size-2, size-2), Piece(Team.BLUE, PieceType.SCISSORS))

    def is_valid_move(self, state: GameState, move: Move) -> bool:
        r1, c1 = move.from_pos
        r2, c2 = move.to_pos
        
        # Check bounds
        if not (0 <= r1 < state.board.size and 0 <= c1 < state.board.size): return False
        if not (0 <= r2 < state.board.size and 0 <= c2 < state.board.size): return False
        
        piece = state.board.get_piece(move.from_pos)
        if piece is None: return False
        if piece.team != state.current_team: return False
        
        # Check 8 directions (distance is exactly 1)
        if max(abs(r1 - r2), abs(c1 - c2)) != 1: return False
        
        # Cannot move to square with friendly piece
        target_piece = state.board.get_piece(move.to_pos)
        if target_piece and target_piece.team == piece.team:
            return False
            
        return True

    def _resolve_combat(self, piece1: Piece, piece2: Piece) -> Piece:
        """Returns the winning piece, or None if both are destroyed."""
        if piece1.piece_type == piece2.piece_type:
            return None # Mutual destruction
            
        # ROCK beats SCISSORS, SCISSORS beats PAPER, PAPER beats ROCK
        win_conditions = {
            PieceType.ROCK: PieceType.SCISSORS,
            PieceType.SCISSORS: PieceType.PAPER,
            PieceType.PAPER: PieceType.ROCK
        }
        
        if win_conditions[piece1.piece_type] == piece2.piece_type:
            return piece1
        return piece2

    def apply_move(self, state: GameState, move: Move):
        moving_piece = state.board.get_piece(move.from_pos)
        target_piece = state.board.get_piece(move.to_pos)
        
        if target_piece:
            # Combat
            winner = self._resolve_combat(moving_piece, target_piece)
            state.board.remove_piece(move.from_pos)
            state.board.set_piece(move.to_pos, winner)
        else:
            # Normal move
            state.board.move_piece(move.from_pos, move.to_pos)
            
        state.move_log.append(move.to_dict())
        
        # Next turn
        state.current_team = Team.BLUE if state.current_team == Team.RED else Team.RED
        if state.current_team == Team.RED:
            state.turn += 1

    def check_winner(self, state: GameState) -> GameResult:
        # Check win condition 1: Reach destination
        # Red destination: a1 (0, 0)
        # Blue destination: i9 (size-1, size-1)
        
        red_dest_piece = state.board.get_piece((0, 0))
        if red_dest_piece and red_dest_piece.team == Team.BLUE:
            return GameResult(ResultType.WIN, Team.BLUE, "Blue reached Red's square (a1)")
            
        blue_dest_piece = state.board.get_piece((state.board.size-1, state.board.size-1))
        if blue_dest_piece and blue_dest_piece.team == Team.RED:
            return GameResult(ResultType.WIN, Team.RED, "Red reached Blue's square (i9)")

        # Check win condition 2: Opponent loses all of one type of piece
        red_counts = {pt: 0 for pt in PieceType}
        blue_counts = {pt: 0 for pt in PieceType}
        
        for r in range(state.board.size):
            for c in range(state.board.size):
                p = state.board.get_piece((r, c))
                if p:
                    if p.team == Team.RED:
                        red_counts[p.piece_type] += 1
                    else:
                        blue_counts[p.piece_type] += 1
                        
        red_missing = any(count == 0 for count in red_counts.values())
        blue_missing = any(count == 0 for count in blue_counts.values())
        
        if red_missing and not blue_missing:
            return GameResult(ResultType.WIN, Team.BLUE, "Red lost all pieces of one type")
        if blue_missing and not red_missing:
            return GameResult(ResultType.WIN, Team.RED, "Blue lost all pieces of one type")
        if red_missing and blue_missing:
            return GameResult(ResultType.DRAW, None, "Both teams lost pieces of one type simultaneously")
            
        # Check max turns
        if state.turn > state.rule_set.max_turns:
            return GameResult(ResultType.DRAW, None, "Max turns reached")
            
        return None

    def play(self, bot_a, bot_b):
        """
        Main game loop simulating a match between two bots (duck typing).
        bot_a is RED, bot_b is BLUE.
        """
        while True:
            winner = self.check_winner(self.state)
            if winner:
                return winner

            current_bot = bot_a if self.state.current_team == Team.RED else bot_b
            
            # Get move from bot
            try:
                move_data = current_bot.get_move(self.state.to_dict())
                move = Move.from_dict(move_data)
            except Exception as e:
                # If bot crashes or returns invalid format, they lose
                losing_team = self.state.current_team
                winning_team = Team.BLUE if losing_team == Team.RED else Team.RED
                return GameResult(ResultType.WIN, winning_team, f"Bot crashed or returned invalid data: {str(e)}")

            if not self.is_valid_move(self.state, move):
                losing_team = self.state.current_team
                winning_team = Team.BLUE if losing_team == Team.RED else Team.RED
                return GameResult(ResultType.WIN, winning_team, "Invalid move")

            self.apply_move(self.state, move)

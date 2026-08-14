from __future__ import annotations
from typing import Optional, List
from dataclasses import dataclass, field

from config import Difficulty, DIFFICULTY_SETTINGS, GRID_SIZES, MAX_TURNS, COLOR_HUMAN, COLOR_AI
from models.board import Board
from models.player import Player, ActionResult
from models.ai_player import AIPlayer


class Game:
    def __init__(self, difficulty: Difficulty = Difficulty.EASY, seed: Optional[int] = None):
        self.difficulty = difficulty
        rows, cols = GRID_SIZES[difficulty]
        self.board = Board(rows, cols, seed=seed)
        self.board.generate(**DIFFICULTY_SETTINGS[difficulty])

        self.human = Player("Human", start=(0, 0), color=COLOR_HUMAN)
        self.ai = AIPlayer("AI", start=(rows - 1, cols - 1), color=COLOR_AI)

        self.turn_count = 0
        self.current_player_is_human = True
        self.game_over = False
        self.winner: Optional[str] = None
        self.log: List[str] = []

    def human_action(self, action: str, **kwargs) -> ActionResult:
        """Dispatch a human action by name. `action` in
        {'move', 'open_door', 'place_obstacle'}."""
        if self.game_over or not self.current_player_is_human:
            return ActionResult(False, "Not the human player's turn.")

        if action == "move":
            result = self.human.move(self.board, kwargs["target"])
        elif action == "open_door":
            result = self.human.open_door(self.board, kwargs["target"])
        elif action == "place_obstacle":
            result = self.human.place_obstacle(self.board, kwargs["target"])
        else:
            return ActionResult(False, f"Unknown action '{action}'.")

        if result.success:
            self._log(result.message)
            self._end_turn()
        return result

    def ai_take_turn(self) -> ActionResult:
        if self.game_over or self.current_player_is_human:
            return ActionResult(False, "Not the AI's turn.")

        result = self.ai.take_turn(self.board)
        self._log(result.message)
        self._end_turn()
        return result

    def _end_turn(self) -> None:
        self.turn_count += 1
        self.board.tick()
        self.current_player_is_human = not self.current_player_is_human
        self._check_game_over()

    def _check_game_over(self) -> None:
        no_treasures_left = len(self.board.treasures()) == 0
        turn_limit_reached = self.turn_count >= MAX_TURNS
        if no_treasures_left or turn_limit_reached:
            self.game_over = True
            if self.human.score > self.ai.score:
                self.winner = self.human.name
            elif self.ai.score > self.human.score:
                self.winner = self.ai.name
            else:
                self.winner = "Draw"
            self._log(
                f"Game over after {self.turn_count} turns. "
                f"Human={self.human.score} AI={self.ai.score}. Winner: {self.winner}"
            )

    def _log(self, message: str) -> None:
        self.log.append(message)
        if len(self.log) > 200:
            self.log.pop(0)

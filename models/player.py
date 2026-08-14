from __future__ import annotations
from typing import Tuple, Optional, List
from dataclasses import dataclass, field

from models.board import Board
from models.treasure import Treasure
from models.trap import Trap
from models.door import Door
from models.powerup import PowerUp
from config import DOOR_COST, STRATEGIC_BONUS, TerrainType

Coord = Tuple[int, int]


@dataclass
class ActionResult:
    success: bool
    message: str
    score_delta: int = 0


class Player:
    def __init__(self, name: str, start: Coord, color=(70, 140, 255)):
        self.name = name
        self.position: Coord = start
        self.color = color
        self.score: int = 0
        self.active_effects: List[str] = []  # e.g. "shield", "speed_boost"
        self.turns_taken: int = 0
        self.treasures_collected: int = 0
        self.traps_hit: int = 0
        self.terrain_delay_turns: int = 0

    # ------------------------------------------------------------------
    # Movement
    # ------------------------------------------------------------------
    def can_move(self, board: Board, target: Coord) -> bool:
        if not board.in_bounds(target):
            return False
        return board.get_tile(*target).is_walkable

    def move(self, board: Board, target: Coord) -> ActionResult:
        if self.terrain_delay_turns > 0:
            self.terrain_delay_turns -= 1
            self.turns_taken += 1
            return ActionResult(True, f"{self.name} is slowed by the terrain and must wait.")

        if not self.can_move(board, target):
            return ActionResult(False, f"{self.name} cannot move to {target}: blocked.")

        self.position = target
        tile = board.get_tile(*target)
        result = ActionResult(True, f"{self.name} moved to {target}.")

        occupant = tile.occupant
        if isinstance(occupant, Door) and occupant.locked:
            occupant.open()
            self.score -= DOOR_COST
            result.message += f" Paid {DOOR_COST} to unlock the door."
            result.score_delta -= DOOR_COST
        elif isinstance(occupant, Treasure) and not occupant.collected:
            gained = occupant.collect()
            self.score += gained
            self.treasures_collected += 1
            tile.occupant = None
            result.message += f" Collected treasure worth {gained}."
            result.score_delta += gained
        elif isinstance(occupant, Trap) and not occupant.triggered:
            if "shield" in self.active_effects:
                self.active_effects.remove("shield")
                result.message += " Shield absorbed a trap!"
            else:
                penalty = occupant.trigger()
                if penalty:
                    self.score += penalty
                    self.traps_hit += 1
                    result.message += f" Hit a trap ({penalty})."
                    result.score_delta += penalty
        elif isinstance(occupant, PowerUp):
            bonus = occupant.collect_bonus()
            self.score += bonus
            self.apply_powerup(occupant)
            tile.occupant = None
            result.message += f" Picked up power-up '{occupant.kind}' (+{bonus})."
            result.score_delta += bonus

        if tile.terrain in (TerrainType.MUD, TerrainType.WATER):
            self.terrain_delay_turns = 1

        self.turns_taken += 1
        return result

    def apply_powerup(self, powerup: PowerUp) -> None:
        self.active_effects.append(powerup.kind)

    # ------------------------------------------------------------------
    # Other actions
    # ------------------------------------------------------------------
    def open_door(self, board: Board, target: Coord) -> ActionResult:
        if not board.in_bounds(target):
            return ActionResult(False, "Target out of bounds.")
        tile = board.get_tile(*target)
        if not isinstance(tile.occupant, Door):
            return ActionResult(False, "No door there.")
        door = tile.occupant
        opened = door.open()
        self.turns_taken += 1
        if opened:
            self.score -= DOOR_COST
            return ActionResult(True, f"{self.name} paid {DOOR_COST} to open the door at {target}.", -DOOR_COST)
        return ActionResult(True, f"Door at {target} was already open.")

    def place_obstacle(self, board: Board, target: Coord, turns: int = 3) -> ActionResult:
        if not board.in_bounds(target):
            return ActionResult(False, "Target out of bounds.")
        if target == self.position:
            return ActionResult(False, "Cannot block your own tile.")
        board.get_tile(*target).place_temp_obstacle(turns)
        self.turns_taken += 1
        return ActionResult(True, f"{self.name} placed a temporary obstacle at {target}.",
                             score_delta=0)

    def block_bonus(self) -> None:
        self.score += STRATEGIC_BONUS

    def __repr__(self) -> str:  # pragma: no cover
        return f"Player({self.name}, pos={self.position}, score={self.score})"

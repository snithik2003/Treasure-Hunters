from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Any

from config import TerrainType, TERRAIN_COST, TERRAIN_WALKABLE


@dataclass
class Tile:
    row: int
    col: int
    terrain: TerrainType = TerrainType.GRASS
    occupant: Optional[Any] = None
    temp_obstacle_turns_left: int = 0
    @property
    def cost(self) -> float:
        return TERRAIN_COST[self.terrain]

    @property
    def is_walkable(self) -> bool:
        if self.temp_obstacle_turns_left > 0:
            return False
        if not TERRAIN_WALKABLE[self.terrain]:
            return False
        # A locked door can be entered and charges the player on entry.
        occ = self.occupant
        if (occ is not None and getattr(occ, "blocks_movement", False)
            and not getattr(occ, "locked", False)):
            return False
        return True

    def place_temp_obstacle(self, turns: int = 3) -> None:
        self.temp_obstacle_turns_left = max(self.temp_obstacle_turns_left, turns)

    def tick(self) -> None:
        if self.temp_obstacle_turns_left > 0:
            self.temp_obstacle_turns_left -= 1

    def __repr__(self) -> str:  # pragma: no cover - convenience only
        occ = type(self.occupant).__name__ if self.occupant else "empty"
        return f"Tile({self.row},{self.col},{self.terrain.value},{occ})"

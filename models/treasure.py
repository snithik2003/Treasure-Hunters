from __future__ import annotations
from dataclasses import dataclass

from config import TREASURE_BASE_VALUE


@dataclass
class Treasure:
    value: int = TREASURE_BASE_VALUE
    blocks_movement: bool = False  # treasures sit on open ground
    collected: bool = False

    def collect(self) -> int:
        self.collected = True
        return self.value

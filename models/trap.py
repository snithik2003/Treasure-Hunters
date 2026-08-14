from __future__ import annotations
from dataclasses import dataclass

from config import TRAP_PENALTY

@dataclass
class Trap:
    blocks_movement: bool = False
    activation_probability: float = 0.75
    triggered: bool = False

    def trigger(self, rng=None) -> int:
        self.triggered = True
        return TRAP_PENALTY

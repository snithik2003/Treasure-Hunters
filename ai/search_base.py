from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import time

from models.board import Board

Coord = Tuple[int, int]


@dataclass
class SearchResult:
    path: List[Coord] = field(default_factory=list)   # start..goal inclusive
    cost: float = 0.0
    expanded_nodes: List[Coord] = field(default_factory=list)  # visited order
    time_seconds: float = 0.0
    found: bool = False
    algorithm_name: str = ""

    @property
    def path_length(self) -> int:
        return max(0, len(self.path) - 1)


class SearchAlgorithm(ABC):
    """Common interface + shared timing wrapper for all path search
    algorithms. Subclasses implement `_search` with the actual logic;
    `search` wraps it with timing so every algorithm reports
    computation time uniformly for the visualizer."""

    name: str = "SearchAlgorithm"

    def search(self, board: Board, start: Coord, goal: Coord) -> SearchResult:
        t0 = time.perf_counter()
        result = self._search(board, start, goal)
        result.time_seconds = time.perf_counter() - t0
        result.algorithm_name = self.name
        return result

    @abstractmethod
    def _search(self, board: Board, start: Coord, goal: Coord) -> SearchResult:
        raise NotImplementedError

    @staticmethod
    def reconstruct_path(came_from: dict, start: Coord, goal: Coord) -> List[Coord]:
        if goal not in came_from and goal != start:
            return []
        path = [goal]
        cur = goal
        while cur != start:
            cur = came_from[cur]
            path.append(cur)
        path.reverse()
        return path

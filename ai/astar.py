from __future__ import annotations
import heapq
import math
from typing import Tuple, Literal

from ai.search_base import SearchAlgorithm, SearchResult
from models.board import Board

Coord = Tuple[int, int]
Heuristic = Literal["manhattan", "euclidean"]


def manhattan(a: Coord, b: Coord) -> float:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def euclidean(a: Coord, b: Coord) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


HEURISTICS = {
    "manhattan": manhattan,
    "euclidean": euclidean,
}


class AStar(SearchAlgorithm):
    name = "A* Search"

    def __init__(self, heuristic: Heuristic = "manhattan"):
        if heuristic not in HEURISTICS:
            raise ValueError(f"Unknown heuristic '{heuristic}'. Choose from {list(HEURISTICS)}.")
        self.heuristic_name = heuristic
        self.heuristic = HEURISTICS[heuristic]

    def _search(self, board: Board, start: Coord, goal: Coord) -> SearchResult:
        # Min-heap of (f_score, tie_breaker, coord)
        counter = 0
        frontier = [(0.0, counter, start)]
        came_from = {}
        g_score = {start: 0.0}
        expanded = []
        closed = set()

        while frontier:
            _, _, current = heapq.heappop(frontier)
            if current in closed:
                continue
            closed.add(current)
            expanded.append(current)

            if current == goal:
                path = self.reconstruct_path(came_from, start, goal)
                return SearchResult(
                    path=path,
                    cost=g_score[goal],
                    expanded_nodes=expanded,
                    found=True,
                )

            for nb in board.walkable_neighbors(current):
                tentative_g = g_score[current] + board.get_tile(*nb).cost
                if nb not in g_score or tentative_g < g_score[nb]:
                    g_score[nb] = tentative_g
                    came_from[nb] = current
                    f = tentative_g + self.heuristic(nb, goal)
                    counter += 1
                    heapq.heappush(frontier, (f, counter, nb))

        return SearchResult(expanded_nodes=expanded, found=False)

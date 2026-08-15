from __future__ import annotations
from collections import deque
from typing import Tuple

from ai.search_base import SearchAlgorithm, SearchResult
from models.board import Board

Coord = Tuple[int, int]


class BFS(SearchAlgorithm):
    name = "Breadth-First Search"

    def _search(self, board: Board, start: Coord, goal: Coord) -> SearchResult:
        frontier = deque([start])
        came_from = {start: None}
        expanded = []

        if start == goal:
            return SearchResult(path=[start], cost=0, expanded_nodes=[start], found=True)

        while frontier:
            current = frontier.popleft()
            expanded.append(current)

            if current == goal:
                path = self.reconstruct_path(came_from, start, goal)
                return SearchResult(
                    path=path,
                    cost=len(path) - 1,  # BFS treats every step as cost 1
                    expanded_nodes=expanded,
                    found=True,
                )

            for nb in board.walkable_neighbors(current):
                if nb not in came_from:
                    came_from[nb] = current
                    frontier.append(nb)

        return SearchResult(expanded_nodes=expanded, found=False)

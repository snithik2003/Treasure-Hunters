from __future__ import annotations
import random
from typing import List, Tuple, Optional, Iterable

from config import TerrainType, TREASURE_BASE_VALUE
from models.tile import Tile
from models.treasure import Treasure
from models.trap import Trap
from models.door import Door
from models.powerup import PowerUp

Coord = Tuple[int, int]


class Board:
    def __init__(self, rows: int, cols: int, seed: Optional[int] = None):
        self.rows = rows
        self.cols = cols
        self._rng = random.Random(seed)
        self.grid: List[List[Tile]] = [
            [Tile(r, c) for c in range(cols)] for r in range(rows)
        ]

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------
    def generate(
        self,
        wall_density: float = 0.12,
        mud_density: float = 0.12,
        water_density: float = 0.08,
        num_treasures: int = 5,
        num_traps: int = 4,
        num_doors: int = 2,
        num_powerups: int = 3,
    ) -> None:

        for r in range(self.rows):
            for c in range(self.cols):
                roll = self._rng.random()
                if roll < wall_density:
                    terrain = TerrainType.WALL
                elif roll < wall_density + mud_density:
                    terrain = TerrainType.MUD
                elif roll < wall_density + mud_density + water_density:
                    terrain = TerrainType.WATER
                else:
                    terrain = TerrainType.GRASS
                self.grid[r][c] = Tile(r, c, terrain)

        # Always keep the two starting corners clear so players can spawn.
        self.grid[0][0] = Tile(0, 0, TerrainType.GRASS)
        self.grid[self.rows - 1][self.cols - 1] = Tile(
            self.rows - 1, self.cols - 1, TerrainType.GRASS
        )

        self._scatter_entities(Treasure, num_treasures, value_range=(20, 100))
        self._scatter_entities(Trap, num_traps)
        self._scatter_entities(Door, num_doors)
        self._scatter_entities(PowerUp, num_powerups)

        self._ensure_connectivity()

    def _scatter_entities(self, cls, count: int, **kwargs) -> None:
        placed = 0
        attempts = 0
        while placed < count and attempts < count * 50:
            attempts += 1
            r = self._rng.randrange(self.rows)
            c = self._rng.randrange(self.cols)
            tile = self.grid[r][c]
            if tile.terrain == TerrainType.WALL:
                continue
            if tile.occupant is not None:
                continue
            if (r, c) in ((0, 0), (self.rows - 1, self.cols - 1)):
                continue
            if cls is Treasure:
                tile.occupant = Treasure(value=TREASURE_BASE_VALUE)
            else:
                tile.occupant = cls()
            placed += 1

    def _ensure_connectivity(self) -> None:
        from collections import deque

        def reachable_from(start: Coord) -> set:
            seen = {start}
            q = deque([start])
            while q:
                cur = q.popleft()
                for nb in self.neighbors(cur):
                    if nb not in seen and self.get_tile(*nb).is_walkable:
                        seen.add(nb)
                        q.append(nb)
            return seen

        reachable = reachable_from((0, 0))
        for r in range(self.rows):
            for c in range(self.cols):
                tile = self.grid[r][c]
                if tile.occupant is not None and isinstance(tile.occupant, Treasure):
                    if (r, c) not in reachable:
                        # Carve a straight-line path of grass tiles.
                        self._carve_path((0, 0), (r, c))
                        reachable = reachable_from((0, 0))

    def _carve_path(self, start: Coord, end: Coord) -> None:
        r, c = start
        er, ec = end
        while r != er:
            r += 1 if er > r else -1
            if self.grid[r][c].terrain == TerrainType.WALL:
                self.grid[r][c].terrain = TerrainType.GRASS
        while c != ec:
            c += 1 if ec > c else -1
            if self.grid[r][c].terrain == TerrainType.WALL:
                self.grid[r][c].terrain = TerrainType.GRASS

    # Queries used heavily by AI search algorithms
    def get_tile(self, row: int, col: int) -> Tile:
        return self.grid[row][col]

    def in_bounds(self, coord: Coord) -> bool:
        r, c = coord
        return 0 <= r < self.rows and 0 <= c < self.cols

    def neighbors(self, coord: Coord) -> Iterable[Coord]:
        r, c = coord
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if self.in_bounds((nr, nc)):
                yield (nr, nc)

    def walkable_neighbors(self, coord: Coord) -> Iterable[Coord]:
        for nb in self.neighbors(coord):
            if self.get_tile(*nb).is_walkable:
                yield nb

    def treasures(self) -> List[Coord]:
        result = []
        for r in range(self.rows):
            for c in range(self.cols):
                if isinstance(self.grid[r][c].occupant, Treasure):
                    result.append((r, c))
        return result

    def tick(self) -> None:
        """Advance per-turn tile effects (temp obstacles decay, etc.)."""
        for row in self.grid:
            for tile in row:
                tile.tick()

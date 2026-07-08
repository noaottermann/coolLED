"""Conway's Game of Life animation for the LED panel."""

from __future__ import annotations

import random
from collections.abc import Iterable

from utils.config import DISPLAY_HEIGHT, DISPLAY_WIDTH
from utils.pixel_math import BLACK, WHITE, Color

from ..animations.base_anim import BaseAnim


class LifeGame(BaseAnim):
    """Game of Life with wraparound-free edges."""

    def __init__(
        self,
        width: int = DISPLAY_WIDTH,
        height: int = DISPLAY_HEIGHT,
        *,
        seed: int | None = None,
        density: float = 0.22,
        start: str | Iterable[tuple[int, int]] | None = None,
    ) -> None:
        super().__init__(width, height, background_color=BLACK)
        self.seed = seed
        self.density = max(0.0, min(1.0, density))
        self.start = start
        self._rng = random.Random(seed)
        self._cells = [[False for _ in range(self.width)] for _ in range(self.height)]
        self.reset()

    def reset(self) -> None:
        """Initialize the board with a randomized population."""
        self._rng = random.Random(self.seed)
        if self.start is None or self.start == "random":
            for y in range(self.height):
                for x in range(self.width):
                    self._cells[y][x] = self._rng.random() < self.density
        elif isinstance(self.start, str):
            self._load_preset(self.start)
        else:
            self._load_custom_start(self.start)
        self._render()

    def _clear_cells(self) -> None:
        for y in range(self.height):
            for x in range(self.width):
                self._cells[y][x] = False

    def _set_cells(self, points: Iterable[tuple[int, int]]) -> None:
        self._clear_cells()
        for x, y in points:
            if 0 <= x < self.width and 0 <= y < self.height:
                self._cells[y][x] = True

    def _load_custom_start(self, points: Iterable[tuple[int, int]]) -> None:
        self._set_cells(points)

    def _load_preset(self, preset: str) -> None:
        center_x = self.width // 2
        center_y = self.height // 2

        if preset == "glider":
            self._set_cells(
                [
                    (center_x, center_y - 1),
                    (center_x + 1, center_y),
                    (center_x - 1, center_y + 1),
                    (center_x, center_y + 1),
                    (center_x + 1, center_y + 1),
                ],
            )
        elif preset in {"cross", "plus"}:
            points = [(center_x, y) for y in range(self.height)] + [(x, center_y) for x in range(self.width)]
            self._set_cells(points)
        elif preset == "checker":
            self._clear_cells()
            for y in range(self.height):
                for x in range(self.width):
                    self._cells[y][x] = (x + y) % 2 == 0
        elif preset == "diamond":
            radius = max(1, min(self.width, self.height) // 4)
            points: list[tuple[int, int]] = []
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if abs(dx) + abs(dy) <= radius:
                        points.append((center_x + dx, center_y + dy))
            self._set_cells(points)
        else:
            raise ValueError(f"Unknown LifeGame start preset: {preset}")

    def _neighbors(self, x: int, y: int) -> int:
        count = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx = x + dx
                ny = y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height and self._cells[ny][nx]:
                    count += 1
        return count

    def _render(self) -> None:
        self.clear()
        for y in range(self.height):
            for x in range(self.width):
                if self._cells[y][x]:
                    self.set_pixel(x, y, WHITE)

    def update(self) -> bool:
        """Advance one generation."""
        next_cells = [[False for _ in range(self.width)] for _ in range(self.height)]
        changed = False

        for y in range(self.height):
            for x in range(self.width):
                alive = self._cells[y][x]
                neighbors = self._neighbors(x, y)
                next_alive = neighbors == 3 or (alive and neighbors == 2)
                next_cells[y][x] = next_alive
                changed = changed or next_alive != alive

        self._cells = next_cells
        self._render()
        return changed

"""Conway's Game of Life animation for the LED panel."""

from __future__ import annotations

import random

from utils.config import DISPLAY_HEIGHT, DISPLAY_WIDTH
from utils.pixel_math import BLACK, WHITE, Color

from ..animations.base_anim import BaseAnim


class LifeGame(BaseAnim):
    """Game of Life with wraparound-free edges."""

    def __init__(self, width: int = DISPLAY_WIDTH, height: int = DISPLAY_HEIGHT, *, seed: int | None = None, density: float = 0.22) -> None:
        super().__init__(width, height, background_color=BLACK)
        self.seed = seed
        self.density = max(0.0, min(1.0, density))
        self._rng = random.Random(seed)
        self._cells = [[False for _ in range(self.width)] for _ in range(self.height)]
        self.reset()

    def reset(self) -> None:
        """Initialize the board with a randomized population."""
        self._rng = random.Random(self.seed)
        for y in range(self.height):
            for x in range(self.width):
                self._cells[y][x] = self._rng.random() < self.density
        self._render()

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

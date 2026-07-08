"""Snake game for the LED panel."""

from __future__ import annotations

import os
import random
from collections import deque
from typing import Literal, cast

from utils.config import DISPLAY_HEIGHT, DISPLAY_WIDTH
from utils.pixel_math import BLACK, WHITE, mix_colors

from ..animations.base_anim import BaseAnim


Direction = tuple[int, int]

try:
    import msvcrt
except ImportError:  # pragma: no cover - Windows-only input support
    msvcrt = None


class Snake(BaseAnim):
    """Autonomous snake that chases food on the LED grid."""

    def __init__(
        self,
        width: int = DISPLAY_WIDTH,
        height: int = DISPLAY_HEIGHT,
        *,
        seed: int | None = None,
        control_mode: Literal["auto", "keyboard"] = "auto",
    ) -> None:
        super().__init__(width, height, background_color=BLACK)
        self.seed = seed
        self.control_mode = control_mode
        self._rng = random.Random(seed)
        self._snake = deque[tuple[int, int]]()
        self._direction: Direction = (1, 0)
        self._next_direction: Direction = (1, 0)
        self._food = (0, 0)
        self.score = 0
        self.reset()

    def reset(self) -> None:
        """Reset the snake and place new food."""
        self._rng = random.Random(self.seed)
        self.score = 0
        self._snake = deque([(self.width // 2, self.height // 2)])
        self._direction = (1, 0)
        self._next_direction = (1, 0)
        self._place_food()
        self._render()

    def _place_food(self) -> None:
        while True:
            food = (self._rng.randrange(self.width), self._rng.randrange(self.height))
            if food not in self._snake:
                self._food = food
                return

    def _choose_direction(self) -> None:
        head_x, head_y = self._snake[0]
        food_x, food_y = self._food
        options: list[Direction] = []

        if food_x > head_x:
            options.append((1, 0))
        elif food_x < head_x:
            options.append((-1, 0))

        if food_y > head_y:
            options.append((0, 1))
        elif food_y < head_y:
            options.append((0, -1))

        fallback = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        for direction in fallback:
            if direction not in options:
                options.append(direction)

        opposite = (-self._direction[0], -self._direction[1])
        for direction in options:
            if direction != opposite:
                self._next_direction = direction
                return

    def _read_keyboard_direction(self) -> Direction | None:
        """Read one arrow-key direction from the keyboard if available."""
        if msvcrt is None:
            return None
        if not msvcrt.kbhit():
            return None

        key = msvcrt.getch()
        if key not in {b"\x00", b"\xe0"}:
            return None

        key = msvcrt.getch()
        mapping: dict[bytes, Direction] = {
            b"H": (0, -1),
            b"P": (0, 1),
            b"K": (-1, 0),
            b"M": (1, 0),
        }
        return mapping.get(key)

    def _apply_keyboard_direction(self) -> None:
        direction = self._read_keyboard_direction()
        if direction is None:
            return

        opposite = (-self._direction[0], -self._direction[1])
        if direction != opposite:
            self._next_direction = direction

    def _render(self) -> None:
        self.clear()
        self.set_pixel(self._food[0], self._food[1], (255, 32, 32))

        snake_length = max(1, len(self._snake) - 1)
        for index, (x, y) in enumerate(self._snake):
            blend = index / snake_length if snake_length else 0.0
            body_color = mix_colors((0, 255, 64), (0, 96, 255), blend)
            self.set_pixel(x, y, body_color)

    def update(self) -> bool:
        """Advance the snake one step toward food."""
        if self.control_mode == "keyboard":
            self._apply_keyboard_direction()
        else:
            self._choose_direction()

        self._direction = self._next_direction

        head_x, head_y = self._snake[0]
        next_head = (head_x + self._direction[0], head_y + self._direction[1])

        if not (0 <= next_head[0] < self.width and 0 <= next_head[1] < self.height):
            self.reset()
            return True

        if next_head in self._snake:
            self.reset()
            return True

        self._snake.appendleft(next_head)

        if next_head == self._food:
            self.score += 1
            self._place_food()
        else:
            self._snake.pop()

        self._render()
        return True

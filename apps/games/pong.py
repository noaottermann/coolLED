"""Simple Pong game for the LED panel."""

from __future__ import annotations

from typing import Literal
import random

try:
    import msvcrt
except ImportError:  # pragma: no cover - Windows-only input support
    msvcrt = None

from utils.config import DISPLAY_HEIGHT, DISPLAY_WIDTH
from utils.pixel_math import BLACK, WHITE, clamp

from ..animations.base_anim import BaseAnim


class Pong(BaseAnim):
    """A tiny autonomous Pong simulation."""

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
        self.paddle_height = max(3, height // 4)
        self.paddle_left = 0
        self.paddle_right = 0
        self.ball_x = 0.0
        self.ball_y = 0.0
        self.ball_dx = 1.0
        self.ball_dy = 1.0
        self.left_score = 0
        self.right_score = 0
        self.reset()

    def reset(self) -> None:
        """Reset paddles, ball, and scores."""
        self._rng = random.Random(self.seed)
        self.left_score = 0
        self.right_score = 0
        self.paddle_left = self.height // 2 - self.paddle_height // 2
        self.paddle_right = self.height // 2 - self.paddle_height // 2
        self._serve(direction=self._rng.choice((-1, 1)))
        self._render()

    def _serve(self, direction: int) -> None:
        self.ball_x = self.width / 2
        self.ball_y = self.height / 2
        self.ball_dx = float(direction)
        self.ball_dy = float(self._rng.choice((-1, 1)))

    def _move_paddles(self) -> None:
        if self.control_mode == "keyboard":
            self._move_keyboard_paddle()
            self._move_ai_paddle()
            return

        left_target = int(self.ball_y) - self.paddle_height // 2
        right_target = int(self.ball_y) - self.paddle_height // 2
        self.paddle_left += clamp(left_target - self.paddle_left, -1, 1)
        self.paddle_right += clamp(right_target - self.paddle_right, -1, 1)
        self.paddle_left = clamp(self.paddle_left, 0, self.height - self.paddle_height)
        self.paddle_right = clamp(self.paddle_right, 0, self.height - self.paddle_height)

    def _move_keyboard_paddle(self) -> None:
        if msvcrt is not None and msvcrt.kbhit():
            key = msvcrt.getch()
            if key in {b"\x00", b"\xe0"}:
                key = msvcrt.getch()
                if key == b"H":
                    self.paddle_left -= 1
                elif key == b"P":
                    self.paddle_left += 1

        self.paddle_left = clamp(self.paddle_left, 0, self.height - self.paddle_height)

    def _move_ai_paddle(self) -> None:
        target = int(self.ball_y) - self.paddle_height // 2
        self.paddle_right += clamp(target - self.paddle_right, -1, 1)
        self.paddle_right = clamp(self.paddle_right, 0, self.height - self.paddle_height)

    def _bounce_vertical(self) -> None:
        if self.ball_y <= 0:
            self.ball_y = 0
            self.ball_dy = abs(self.ball_dy)
        elif self.ball_y >= self.height - 1:
            self.ball_y = self.height - 1
            self.ball_dy = -abs(self.ball_dy)

    def _score_point(self, left_player_scores: bool) -> None:
        if left_player_scores:
            self.left_score += 1
            self._serve(direction=1)
        else:
            self.right_score += 1
            self._serve(direction=-1)

    def _render(self) -> None:
        self.clear()

        for y in range(self.paddle_height):
            self.set_pixel(1, self.paddle_left + y, WHITE)
            self.set_pixel(self.width - 2, self.paddle_right + y, WHITE)

        self.set_pixel(int(round(self.ball_x)), int(round(self.ball_y)), (255, 64, 64))

    def update(self) -> bool:
        """Advance the pong simulation by one tick."""
        self._move_paddles()

        self.ball_x += self.ball_dx
        self.ball_y += self.ball_dy

        self._bounce_vertical()

        if self.ball_x <= 2:
            if self.paddle_left <= self.ball_y <= self.paddle_left + self.paddle_height - 1:
                self.ball_x = 2
                self.ball_dx = abs(self.ball_dx)
            else:
                self._score_point(left_player_scores=False)
        elif self.ball_x >= self.width - 3:
            if self.paddle_right <= self.ball_y <= self.paddle_right + self.paddle_height - 1:
                self.ball_x = self.width - 3
                self.ball_dx = -abs(self.ball_dx)
            else:
                self._score_point(left_player_scores=True)

        self._render()
        return True

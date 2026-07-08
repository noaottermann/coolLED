"""More advanced display smoke test for the CoolLED matrix."""

from __future__ import annotations

import asyncio
from typing import Iterable

from apps.animations.animation_engine import AnimationEngine, AnimationEngineConfig
from apps.animations.base_anim import BaseAnim
from core.ble_manager import BleManager
from utils.config import DISPLAY_HEIGHT, DISPLAY_WIDTH, MAC_ADDRESS
from utils.pixel_math import BLACK, WHITE, add_colors, grayscale, invert_color, mix_colors, scale_color


class ComplexDisplayTest(BaseAnim):
    """A richer framebuffer test that exercises multiple pixel operations."""

    def __init__(self, width: int, height: int) -> None:
        super().__init__(width, height, background_color=BLACK)
        self.tick = 0
        self._wave_row = height // 2

    def _draw_border(self) -> None:
        border_color = (0, 96, 255)
        for x in range(self.width):
            self.set_pixel(x, 0, border_color)
            self.set_pixel(x, self.height - 1, border_color)
        for y in range(self.height):
            self.set_pixel(0, y, border_color)
            self.set_pixel(self.width - 1, y, border_color)

    def _draw_diagonal(self) -> None:
        for x in range(self.width):
            y = (x + self.tick) % self.height
            self.set_pixel(x, y, invert_color((32, 32, 32)))

    def _draw_center_cross(self) -> None:
        cross_color = mix_colors((255, 64, 0), (255, 255, 0), 0.35)
        mid_x = self.width // 2
        mid_y = self.height // 2
        for x in range(self.width):
            self.set_pixel(x, mid_y, cross_color)
        for y in range(self.height):
            self.set_pixel(mid_x, y, cross_color)

    def _draw_wave(self) -> None:
        base_color = grayscale((40, 220, 120))
        for x in range(self.width):
            y = (self._wave_row + ((x + self.tick) % 4) - 2)
            if 0 <= y < self.height:
                self.set_pixel(x, y, scale_color(base_color, 1.15))
                if y + 1 < self.height:
                    self.set_pixel(x, y + 1, scale_color(base_color, 0.7))

    def update(self) -> bool:
        self.clear()
        self._draw_border()
        self._draw_diagonal()
        self._draw_center_cross()
        self._draw_wave()

        highlight = add_colors((8, 8, 8), (48, 0, 96))
        self.set_pixel(self.tick % self.width, self.tick % self.height, WHITE)
        self.set_pixel((self.tick * 2) % self.width, (self.height - 1) - (self.tick % self.height), highlight)

        self.tick += 1
        if self.tick % 16 == 0:
            self._wave_row = (self._wave_row + 1) % self.height
        return True


async def main() -> None:
    manager = BleManager(address=MAC_ADDRESS, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT)
    animation = ComplexDisplayTest(DISPLAY_WIDTH, DISPLAY_HEIGHT)
    engine = AnimationEngine(manager, animation, config=AnimationEngineConfig(fps=12.0))

    try:
        await engine.run(max_frames=120)
    except Exception as exc:
        print(f"[test_display2] run failed: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
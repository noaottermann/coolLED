"""Runtime helper for driving framebuffer-based animations on the LED panel."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Optional

from core.ble_manager import BleManager

from .base_anim import BaseAnim


@dataclass(slots=True)
class AnimationEngineConfig:
    """Runtime settings for the animation loop."""

    fps: float = 30.0
    auto_connect: bool = True
    auto_disconnect: bool = True
    power_on_before_run: bool = True


class AnimationEngine:
    """Drive a `BaseAnim` instance and push frames to the display."""

    def __init__(self, ble_manager: BleManager, animation: BaseAnim, *, config: AnimationEngineConfig | None = None) -> None:
        self.ble_manager = ble_manager
        self.animation = animation
        self.config = config or AnimationEngineConfig()
        self._stop_requested = False

    @property
    def frame_delay(self) -> float:
        """Return the number of seconds to wait between frames."""
        if self.config.fps <= 0:
            return 0.0
        return 1.0 / self.config.fps

    def stop(self) -> None:
        """Request that the loop exits after the current frame."""
        self._stop_requested = True

    async def connect(self) -> None:
        """Connect the BLE manager if needed."""
        if self.config.auto_connect and not self.ble_manager.is_connected:
            await self.ble_manager.connect()

    async def disconnect(self) -> None:
        """Disconnect the BLE manager if needed."""
        if self.config.auto_disconnect and self.ble_manager.is_connected:
            await self.ble_manager.disconnect()

    async def show_current_frame(self) -> None:
        """Push the current animation framebuffer to the display."""
        await self.ble_manager.show_buffer(self.animation.frame())

    async def step(self) -> bool:
        """Advance the animation once and display the resulting frame."""
        changed = self.animation.update()
        await self.show_current_frame()
        return changed

    async def run(self, *, max_frames: Optional[int] = None, duration: float | None = None) -> None:
        """Run the animation until stopped, a frame limit is reached, or time elapses."""
        await self.connect()

        if self.config.power_on_before_run:
            await self.ble_manager.set_power(True)

        frames_rendered = 0
        loop = asyncio.get_running_loop()
        started_at = loop.time()

        try:
            while not self._stop_requested:
                if max_frames is not None and frames_rendered >= max_frames:
                    break
                if duration is not None and loop.time() - started_at >= duration:
                    break

                await self.step()
                frames_rendered += 1

                if self.frame_delay > 0:
                    await asyncio.sleep(self.frame_delay)
        finally:
            self._stop_requested = False
            await self.disconnect()

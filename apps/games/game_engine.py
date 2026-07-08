"""Reusable game loop for framebuffer-based LED games."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from core.ble_manager import BleManager


@runtime_checkable
class GameProtocol(Protocol):
    """Protocol for game objects that can be driven by the engine."""

    width: int
    height: int

    def reset(self) -> None:
        """Reset the game state to the initial condition."""

    def update(self) -> bool:
        """Advance the game state by one tick. Return True if the frame changed."""

    def frame(self):
        """Return a 2D RGB framebuffer for the current game state."""


@dataclass(slots=True)
class GameEngineConfig:
    """Runtime settings for the game loop."""

    fps: float = 15.0
    auto_connect: bool = True
    auto_disconnect: bool = True
    power_on_before_run: bool = True


class GameEngine:
    """Drive a game object and present its framebuffer on the LED panel."""

    def __init__(self, ble_manager: BleManager, game: GameProtocol, *, config: GameEngineConfig | None = None) -> None:
        self.ble_manager = ble_manager
        self.game = game
        self.config = config or GameEngineConfig()
        self._stop_requested = False

    @property
    def frame_delay(self) -> float:
        """Return the delay between frames in seconds."""
        if self.config.fps <= 0:
            return 0.0
        return 1.0 / self.config.fps

    def stop(self) -> None:
        """Request that the loop exit after the current frame."""
        self._stop_requested = True

    async def connect(self) -> None:
        """Connect the BLE manager if requested."""
        if self.config.auto_connect and not self.ble_manager.is_connected:
            await self.ble_manager.connect()

    async def disconnect(self) -> None:
        """Disconnect the BLE manager if requested."""
        if self.config.auto_disconnect and self.ble_manager.is_connected:
            await self.ble_manager.disconnect()

    async def show_current_frame(self) -> None:
        """Push the current game framebuffer to the display."""
        await self.ble_manager.show_buffer(self.game.frame())

    async def step(self) -> bool:
        """Advance the game once and send the frame to the display."""
        changed = self.game.update()
        await self.show_current_frame()
        return changed

    async def run(self, *, max_frames: int | None = None, duration: float | None = None) -> None:
        """Run the game loop until stopped, bounded by frames or time if provided."""
        await self.connect()

        if self.config.power_on_before_run:
            await self.ble_manager.set_power(True)

        self.game.reset()
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
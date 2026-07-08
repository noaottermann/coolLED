"""Display selectable mathematical function graphs on the LED panel."""

from __future__ import annotations

import argparse
import asyncio
import math
from dataclasses import dataclass
from typing import Callable

from apps.animations.animation_engine import AnimationEngine, AnimationEngineConfig
from apps.animations.base_anim import BaseAnim
from core.ble_manager import BleManager
from utils.config import DISPLAY_HEIGHT, DISPLAY_WIDTH, MAC_ADDRESS
from utils.pixel_math import BLACK, WHITE, add_colors, clamp


GraphFunction = Callable[[float], float]


def _safe_tan(value: float) -> float:
    """Return a clipped tangent value so the graph remains readable."""
    result = math.tan(value)
    return max(-4.0, min(4.0, result))


FUNCTIONS: dict[str, GraphFunction] = {
    "sin": lambda x: math.sin(x * math.pi),
    "cos": lambda x: math.cos(x * math.pi),
    "tan": lambda x: _safe_tan(x * math.pi / 2),
    "parabola": lambda x: x * x,
    "cubic": lambda x: x * x * x,
    "abs": lambda x: abs(x) * 2 - 1,
    "sqrt": lambda x: math.sqrt(max(0.0, x + 1.0)) - 1.0,
    "wave": lambda x: math.sin(x * math.pi * 2) * 0.7 + math.sin(x * math.pi * 5) * 0.25,
}


@dataclass(slots=True)
class FunctionGraphConfig:
    """Settings for the graph plotting animation."""

    function_name: str = "sin"
    color: tuple[int, int, int] = (0, 255, 96)
    grid_color: tuple[int, int, int] = (32, 32, 32)
    axis_color: tuple[int, int, int] = (96, 96, 96)
    point_color: tuple[int, int, int] = WHITE
    animate_phase: bool = True
    phase_step: float = 0.08


class FunctionGraphAnimation(BaseAnim):
    """Render a mathematical function as a graph on the LED matrix."""

    def __init__(
        self,
        width: int,
        height: int,
        *,
        function_name: str = "sin",
        animate_phase: bool = True,
        phase_step: float = 0.08,
        line_color: tuple[int, int, int] = (0, 255, 96),
        grid_color: tuple[int, int, int] = (32, 32, 32),
        axis_color: tuple[int, int, int] = (96, 96, 96),
        point_color: tuple[int, int, int] = WHITE,
    ) -> None:
        super().__init__(width, height, background_color=BLACK)
        if function_name not in FUNCTIONS:
            raise ValueError(f"Unknown function '{function_name}'. Available: {', '.join(sorted(FUNCTIONS))}")
        self.function_name = function_name
        self.function = FUNCTIONS[function_name]
        self.animate_phase = animate_phase
        self.phase_step = phase_step
        self.line_color = line_color
        self.grid_color = grid_color
        self.axis_color = axis_color
        self.point_color = point_color
        self.phase = 0.0
        self.reset()

    def reset(self) -> None:
        """Reset the graph phase and redraw the frame."""
        self.phase = 0.0
        self._render()

    def _draw_grid(self) -> None:
        mid_x = self.width // 2
        mid_y = self.height // 2

        for x in range(self.width):
            if x % 4 == 0:
                self.set_pixel(x, mid_y, self.grid_color)
        for y in range(self.height):
            if y % 4 == 0:
                self.set_pixel(mid_x, y, self.grid_color)

        for x in range(self.width):
            self.set_pixel(x, mid_y, self.axis_color)
        for y in range(self.height):
            self.set_pixel(mid_x, y, self.axis_color)

    def _graph_points(self) -> list[tuple[int, int]]:
        points: list[tuple[int, int]] = []
        amplitude = max(1.0, (self.height - 4) / 4.0)
        mid_y = self.height / 2.0

        for x in range(self.width):
            normalized_x = (x / (self.width - 1) if self.width > 1 else 0.0) * 2.0 - 1.0
            sample_x = normalized_x + self.phase
            value = self.function(sample_x)
            y = round(mid_y - value * amplitude)
            points.append((x, clamp(y, 0, self.height - 1)))

        return points

    def _render(self) -> None:
        self.clear()
        self._draw_grid()

        points = self._graph_points()
        for index, (x, y) in enumerate(points):
            self.set_pixel(x, y, self.line_color)

            if index > 0:
                previous_x, previous_y = points[index - 1]
                if previous_y != y:
                    step = 1 if y > previous_y else -1
                    for intermediate_y in range(previous_y, y, step):
                        self.set_pixel(x, intermediate_y, add_colors(self.line_color, (16, 16, 16)))

        center_x = self.width // 2
        center_y = self.height // 2
        self.set_pixel(center_x, center_y, self.point_color)

    def update(self) -> bool:
        """Advance the phase and redraw the graph."""
        if self.animate_phase:
            self.phase += self.phase_step
        self._render()
        return True


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description="Display a graph of a mathematical function on the CoolLED panel")
    parser.add_argument("function", nargs="?", default="sin", choices=sorted(FUNCTIONS), help="Function to plot")
    parser.add_argument("--address", default=MAC_ADDRESS, help="BLE MAC address")
    parser.add_argument("--width", type=int, default=DISPLAY_WIDTH, help="Display width in pixels")
    parser.add_argument("--height", type=int, default=DISPLAY_HEIGHT, help="Display height in pixels")
    parser.add_argument("--fps", type=float, default=12.0, help="Animation frame rate")
    parser.add_argument("--duration", type=float, default=None, help="Optional run duration in seconds")
    parser.add_argument("--no-animate-phase", action="store_true", help="Render a static graph without moving the phase")
    parser.add_argument("--phase-step", type=float, default=0.08, help="Phase advance per frame when animating")
    parser.add_argument("--line-color", default="#00ff60", help="Graph line color")
    parser.add_argument("--grid-color", default="#202020", help="Grid color")
    parser.add_argument("--axis-color", default="#606060", help="Axis color")
    parser.add_argument("--point-color", default="#ffffff", help="Center point color")
    return parser


async def run_demo(args: argparse.Namespace) -> None:
    """Run the graph animation on the LED panel."""
    ble_manager = BleManager(address=args.address, width=args.width, height=args.height)
    animation = FunctionGraphAnimation(
        args.width,
        args.height,
        function_name=args.function,
        animate_phase=not args.no_animate_phase,
        phase_step=args.phase_step,
        line_color=_parse_color(args.line_color),
        grid_color=_parse_color(args.grid_color),
        axis_color=_parse_color(args.axis_color),
        point_color=_parse_color(args.point_color),
    )
    engine = AnimationEngine(ble_manager, animation, config=AnimationEngineConfig(fps=args.fps))
    await engine.run(duration=args.duration)


def _parse_color(value: str) -> tuple[int, int, int]:
    """Parse a PIL-compatible color string into an RGB tuple."""
    from PIL import ImageColor

    return tuple(ImageColor.getrgb(value))


def main() -> int:
    """Run the function graph demo."""
    parser = build_parser()
    args = parser.parse_args()
    asyncio.run(run_demo(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
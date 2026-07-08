"""Entry point for a simple scrolling text demo."""

from __future__ import annotations

import argparse
import asyncio

from apps.animations.animation_engine import AnimationEngine, AnimationEngineConfig
from apps.animations.scroller import Scroller
from core.ble_manager import BleManager
from utils.config import DISPLAY_HEIGHT, DISPLAY_WIDTH, MAC_ADDRESS


def build_parser() -> argparse.ArgumentParser:
	"""Build the command-line parser for the demo."""
	parser = argparse.ArgumentParser(description="CoolLED scrolling text demo")
	parser.add_argument("text", nargs="?", default="Hello from CoolLED", help="Text to scroll")
	parser.add_argument("--address", default=MAC_ADDRESS, help="BLE MAC address")
	parser.add_argument("--width", type=int, default=DISPLAY_WIDTH, help="Display width in pixels")
	parser.add_argument("--height", type=int, default=DISPLAY_HEIGHT, help="Display height in pixels")
	parser.add_argument("--fps", type=float, default=30.0, help="Animation frame rate")
	parser.add_argument("--speed", type=int, default=1, help="Scroll speed in pixels per frame")
	parser.add_argument("--duration", type=float, default=None, help="Optional run duration in seconds")
	parser.add_argument("--font", default="arial", help="Font name for the scroller")
	parser.add_argument("--font-height", type=int, default=13, help="Font height for the scroller")
	parser.add_argument("--color", default="white", help="Text color")
	parser.add_argument("--background-color", default="black", help="Background color")
	return parser


async def run_demo(args: argparse.Namespace) -> None:
	"""Create the animation objects and run them."""
	ble_manager = BleManager(address=args.address, width=args.width, height=args.height)
	animation = Scroller(
		args.text,
		args.width,
		args.height,
		color=args.color,
		background_color=args.background_color,
		font=args.font,
		font_height=args.font_height,
		speed=args.speed,
	)
	engine = AnimationEngine(
		ble_manager,
		animation,
		config=AnimationEngineConfig(fps=args.fps),
	)
	await engine.run(duration=args.duration)


def main() -> int:
	"""Run the scrolling text demo."""
	parser = build_parser()
	args = parser.parse_args()
	asyncio.run(run_demo(args))
	return 0


if __name__ == "__main__":
	raise SystemExit(main())

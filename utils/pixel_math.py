"""Small RGB math helpers used by animations and display code."""

from __future__ import annotations

from typing import Iterable, Sequence

Color = tuple[int, int, int]

BLACK: Color = (0, 0, 0)
WHITE: Color = (255, 255, 255)


def clamp(value: int, minimum: int = 0, maximum: int = 255) -> int:
	"""Clamp an integer into the inclusive range [minimum, maximum]."""
	return max(minimum, min(maximum, value))


def clamp_color(color: Sequence[int]) -> Color:
	"""Clamp an RGB sequence into a valid 8-bit color triple."""
	return tuple(clamp(channel) for channel in color[:3])  # type: ignore[return-value]


def add_colors(first: Sequence[int], second: Sequence[int]) -> Color:
	"""Add two colors with 8-bit saturation."""
	return tuple(
		clamp(a + b)
		for a, b in zip(first[:3], second[:3], strict=False)
	)  # type: ignore[return-value]


def scale_color(color: Sequence[int], factor: float) -> Color:
	"""Scale a color by a floating-point factor."""
	return tuple(clamp(round(channel * factor)) for channel in color[:3])  # type: ignore[return-value]


def lerp(start: int, end: int, amount: float) -> int:
	"""Linearly interpolate between two integers."""
	return round(start + (end - start) * amount)


def mix_colors(first: Sequence[int], second: Sequence[int], amount: float) -> Color:
	"""Blend two RGB colors together."""
	amount = max(0.0, min(1.0, amount))
	return tuple(
		lerp(a, b, amount)
		for a, b in zip(first[:3], second[:3], strict=False)
	)  # type: ignore[return-value]


def invert_color(color: Sequence[int]) -> Color:
	"""Invert an RGB color."""
	return tuple(255 - clamp(channel) for channel in color[:3])  # type: ignore[return-value]


def grayscale(color: Sequence[int]) -> Color:
	"""Convert a color to a grayscale RGB triple."""
	value = round(sum(clamp(channel) for channel in color[:3]) / 3)
	return (value, value, value)


def fill_buffer(width: int, height: int, color: Sequence[int] = BLACK) -> list[list[Color]]:
	"""Build a 2D RGB buffer filled with one color."""
	fill_color = clamp_color(color)
	return [[fill_color for _ in range(width)] for _ in range(height)]


def copy_buffer(buffer: Sequence[Sequence[Sequence[int]]]) -> list[list[Color]]:
	"""Deep-copy a 2D RGB buffer."""
	return [
		[clamp_color(pixel) for pixel in row]
		for row in buffer
	]


def iter_pixels(buffer: Sequence[Sequence[Sequence[int]]]):
	"""Yield x, y, color tuples from a 2D RGB buffer."""
	for y, row in enumerate(buffer):
		for x, pixel in enumerate(row):
			yield x, y, clamp_color(pixel)

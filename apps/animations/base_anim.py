"""Base classes for framebuffer-driven animations."""

from __future__ import annotations

import abc
from typing import Iterable, Sequence

from PIL import Image

from utils.pixel_math import BLACK, Color, clamp_color, copy_buffer, fill_buffer


class BaseAnim(abc.ABC):
	"""Base class for simple animations built on a local RGB buffer."""

	def __init__(
		self,
		width: int,
		height: int,
		*,
		background_color: Sequence[int] = BLACK,
	) -> None:
		self.width = width
		self.height = height
		self.background_color: Color = clamp_color(background_color)
		self.buffer = fill_buffer(width, height, self.background_color)

	def clear(self) -> None:
		"""Reset the buffer to the background color."""
		self.buffer = fill_buffer(self.width, self.height, self.background_color)

	def fill(self, color: Sequence[int]) -> None:
		"""Fill the whole buffer with one color."""
		self.buffer = fill_buffer(self.width, self.height, color)

	def set_pixel(self, x: int, y: int, color: Sequence[int]) -> None:
		"""Set a pixel if the coordinate is inside the buffer."""
		if 0 <= x < self.width and 0 <= y < self.height:
			self.buffer[y][x] = clamp_color(color)

	def get_pixel(self, x: int, y: int) -> Color:
		"""Read a pixel from the buffer."""
		if 0 <= x < self.width and 0 <= y < self.height:
			return self.buffer[y][x]
		return self.background_color

	def copy_buffer(self) -> list[list[Color]]:
		"""Return a deep copy of the current framebuffer."""
		return copy_buffer(self.buffer)

	def to_image(self) -> Image.Image:
		"""Convert the current buffer into a PIL image."""
		image = Image.new("RGB", (self.width, self.height), self.background_color)
		for y, row in enumerate(self.buffer):
			for x, pixel in enumerate(row):
				image.putpixel((x, y), pixel)
		return image

	def draw_points(self, points: Iterable[tuple[int, int, Sequence[int]]]) -> None:
		"""Draw a set of points into the buffer."""
		for x, y, color in points:
			self.set_pixel(x, y, color)

	@abc.abstractmethod
	def update(self) -> bool:
		"""Advance the animation state by one step. Return True if the frame changed."""

	def frame(self) -> list[list[Color]]:
		"""Return the current frame buffer."""
		return self.copy_buffer()

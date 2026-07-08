"""Scrolling text animation for the LED panel."""

from __future__ import annotations

from PIL import Image

from coolledx import DEFAULT_BACKGROUND_COLOR, DEFAULT_COLOR, DEFAULT_FONT, DEFAULT_FONT_SIZE
from coolledx.render import render_text_to_image

from utils.pixel_math import BLACK, Color, clamp_color

from .base_anim import BaseAnim


class Scroller(BaseAnim):
	"""Render a text string and scroll it across the framebuffer."""

	def __init__(
		self,
		text: str,
		width: int,
		height: int,
		*,
		color: str = DEFAULT_COLOR,
		background_color: str = DEFAULT_BACKGROUND_COLOR,
		font: str = DEFAULT_FONT,
		font_height: int = DEFAULT_FONT_SIZE,
		speed: int = 1,
		loop: bool = True,
	) -> None:
		super().__init__(width, height, background_color=ImageColorToRGB(background_color))
		self.text = text
		self.color = color
		self.background_color_name = background_color
		self.font = font
		self.font_height = font_height
		self.speed = max(1, speed)
		self.loop = loop
		self._offset = 0
		self._surface = self._build_surface()
		self._reset_offset()

	def _build_surface(self) -> Image.Image:
		"""Create a scrollable image that contains the rendered text."""
		text_image = render_text_to_image(
			self.text,
			default_color=self.color,
			font=self.font,
			font_height=self.font_height,
			background_color=self.background_color_name,
		).convert("RGB")

		surface_width = self.width + text_image.width + self.width
		surface = Image.new("RGB", (surface_width, self.height), self.background_color)
		y_offset = max(0, (self.height - text_image.height) // 2)
		surface.paste(text_image, (self.width, y_offset))
		return surface

	def _reset_offset(self) -> None:
		self._offset = 0
		self._render_frame()

	def _render_frame(self) -> None:
		"""Copy the current visible window into the framebuffer."""
		window = self._surface.crop((self._offset, 0, self._offset + self.width, self.height))
		self.clear()
		for y in range(min(self.height, window.height)):
			for x in range(min(self.width, window.width)):
				self.set_pixel(x, y, window.getpixel((x, y)))

	def set_text(self, text: str) -> None:
		"""Replace the displayed text and restart the scroll position."""
		self.text = text
		self._surface = self._build_surface()
		self._reset_offset()

	def update(self) -> bool:
		"""Advance the scroll position by one step."""
		if self._surface.width <= self.width:
			self._render_frame()
			return False

		previous_offset = self._offset
		self._offset += self.speed

		max_offset = self._surface.width - self.width
		if self._offset > max_offset:
			self._offset = 0 if self.loop else max_offset

		self._render_frame()
		return self._offset != previous_offset


def ImageColorToRGB(color_name: str) -> Color:
	"""Convert a PIL color name into an RGB tuple."""
	from PIL import ImageColor

	return clamp_color(ImageColor.getrgb(color_name))

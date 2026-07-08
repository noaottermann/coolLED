"""Async BLE helper for sending CoolLED commands."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Iterable, Sequence

from PIL import Image

from coolledx.client import Client
from coolledx.commands import SetBrightness, SetImage, TurnOnOffApp
from utils.config import DISPLAY_HEIGHT, DISPLAY_WIDTH, MAC_ADDRESS


class BleManager:
	"""Small convenience wrapper around the vendored CoolLED client."""

	def __init__(
		self,
		address: str | None = MAC_ADDRESS,
		*,
		width: int = DISPLAY_WIDTH,
		height: int = DISPLAY_HEIGHT,
		connection_timeout: float = 10.0,
		command_timeout: float = 1.0,
		connection_retries: int = 5,
	) -> None:
		self.address = address
		self.width = width
		self.height = height
		self.client = Client(
			address=address,
			connection_timeout=connection_timeout,
			command_timeout=command_timeout,
			connection_retries=connection_retries,
		)
		self.is_connected = False

	async def __aenter__(self) -> "BleManager":
		await self.connect()
		return self

	async def __aexit__(self, exc_type, exc, tb) -> None:
		await self.disconnect()

	async def connect(self) -> bool:
		"""Connect to the sign and mark the manager as ready."""
		try:
			await self.client.connect()
		except Exception:
			self.is_connected = False
			raise

		self.is_connected = True
		return True

	async def disconnect(self) -> None:
		"""Disconnect from the sign if a session is active."""
		if not self.is_connected:
			return
		try:
			await self.client.disconnect()
		finally:
			self.is_connected = False

	async def send_command(self, command) -> None:
		"""Forward a command to the underlying client."""
		await self.client.send_command(command)

	async def set_power(self, on: bool) -> None:
		"""Turn the display on or off."""
		await self.send_command(TurnOnOffApp(on=on))

	async def set_brightness(self, level: int) -> None:
		"""Set the display brightness."""
		level = max(0, min(255, level))
		await self.send_command(SetBrightness(brightness=level))

	def buffer_to_image(self, buffer: Sequence[Sequence[Sequence[int]]]) -> Image.Image:
		"""Convert an RGB framebuffer into a PIL image."""
		image = Image.new("RGB", (self.width, self.height), (0, 0, 0))
		for y, row in enumerate(buffer):
			if y >= self.height:
				break
			for x, color in enumerate(row):
				if x >= self.width:
					break
				image.putpixel((x, y), tuple(color[:3]))
		return image

	async def show_image(self, image: Image.Image) -> None:
		"""Send a PIL image to the display through SetImage."""
		temp_path: Path | None = None
		try:
			with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
				temp_path = Path(temp_file.name)
			image.save(temp_path)
			await self.send_command(SetImage(str(temp_path)))
		finally:
			if temp_path and temp_path.exists():
				temp_path.unlink()

	async def show_buffer(self, buffer: Sequence[Sequence[Sequence[int]]]) -> None:
		"""Convert a framebuffer and send it to the display."""
		await self.show_image(self.buffer_to_image(buffer))

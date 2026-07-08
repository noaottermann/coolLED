import os
import tempfile
import asyncio
from pathlib import Path
from typing import List, Tuple
from PIL import Image

from coolledx.client import Client
from coolledx.commands import SetImage, TurnOnOffApp, SetBrightness
from utils.config import DISPLAY_HEIGHT, DISPLAY_WIDTH, MAC_ADDRESS

class MatrixDisplay:
    def __init__(self, mac_address: str = MAC_ADDRESS, width: int = DISPLAY_WIDTH, height: int = DISPLAY_HEIGHT):
        self.mac_address = mac_address
        self.width = width
        self.height = height

        self.client = Client(address=self.mac_address)
        self.is_connected = False

        self.buffer: List[List[Tuple[int, int, int]]] = []
        self.clear_buffer()

    def clear_buffer(self):
        """Réinitialise le buffer interne en noir sans l'envoyer immédiatement."""
        self.buffer = [[(0, 0, 0) for _ in range(self.width)] for _ in range(self.height)]

    async def connect(self) -> bool:
        """Establish the BLE connection to the LED matrix."""
        try:
            print(f"[BLE] Connecting to matrix {self.mac_address} via coolledx...")
            await self.client.connect()
            self.is_connected = True
            print("[BLE] Connected successfully.")
            return True
        except Exception as e:
            print(f"[BLE] Connection failed: {e}")
            self.is_connected = False
            return False

    async def disconnect(self):
        """Close the Bluetooth session cleanly."""
        if self.is_connected:
            try:
                await self.client.disconnect()
                print("[BLE] Disconnected successfully.")
            except Exception as e:
                print(f"[BLE] Disconnect error: {e}")
            finally:
                self.is_connected = False

    def set_pixel(self, x: int, y: int, color: Tuple[int, int, int]):
        """Change one pixel in the local framebuffer."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.buffer[y][x] = color

    def fill(self, color: Tuple[int, int, int]):
        """Fill the whole screen with one color."""
        self.buffer = [[color for _ in range(self.width)] for _ in range(self.height)]

    def clear(self):
        """Turn every pixel off in the local framebuffer."""
        self.fill((0, 0, 0))

    async def set_power(self, on: bool):
        """Turn the matrix display on or off through the command API."""
        if not self.is_connected:
            return
        cmd = TurnOnOffApp(on=on)
        await self.client.send_command(cmd)

    def _buffer_to_image(self) -> Image.Image:
        """Convert the framebuffer into a PIL image."""
        image = Image.new("RGB", (self.width, self.height), (0, 0, 0))
        for y, row in enumerate(self.buffer):
            for x, color in enumerate(row):
                image.putpixel((x, y), color)
        return image

    async def show(self):
        """Send the current framebuffer to the physical matrix."""
        if not self.is_connected:
            print("[WARN] Cannot display: matrix is not connected.")
            return
        temp_path: Path | None = None
        try:
            image = self._buffer_to_image()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                temp_path = temp_file.name
            image.save(temp_path)
            await self.client.send_command(SetImage(temp_path))
        except Exception as e:
            print(f"[BLE] Frame transmission error: {e}")
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
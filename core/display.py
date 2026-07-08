import os
import tempfile
import asyncio
from typing import List, Tuple
from PIL import Image

from coolledx.client import Client
from coolledx.commands import SetImage, TurnOnOffApp, SetBrightness

class MatrixDisplay:
    def __init__(self, mac_address: str = "FF:00:00:04:1B:DF", width: int = 64, height: int = 16):
        self.mac_address = mac_address
        self.width = width
        self.height = height

        self.client = Client(address=self.mac_address)
        self.is_connected = False

        self.buffer: List[List[Tuple[int, int, int]]] = []
        self.clear_buffer()

    def clear_buffer(self):
        self.buffer = [[(0, 0, 0) for _ in range(self.width)] for _ in range(self.height)]

    async def connect(self) -> bool:
        try:
            print(f"[BLE] Connexion à la matrice {self.mac_address} via coolledx...")
            await self.client.connect()
            
            # 👇 FIX WINDOWS : On laisse la pile BLE s'initialiser correctement
            print("[BLE] Négociation BLE en cours, attente de 2 secondes...")
            await asyncio.sleep(2.0) 
            
            self.is_connected = True
            print("[BLE] Connecté avec succès. Matériel auto-détecté !")
            return True
        except Exception as e:
            print(f"[BLE] Échec de la connexion : {e}")
            self.is_connected = False
            return False

    async def disconnect(self):
        if self.is_connected:
            try:
                await self.client.disconnect()
                print("[BLE] Déconnecté avec succès.")
            except Exception as e:
                print(f"[BLE] Erreur de déconnexion : {e}")
            finally:
                self.is_connected = False

    def set_pixel(self, x: int, y: int, color: Tuple[int, int, int]):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.buffer[y][x] = color

    def fill(self, color: Tuple[int, int, int]):
        self.buffer = [[color for _ in range(self.width)] for _ in range(self.height)]

    def clear(self):
        self.fill((0, 0, 0))

    async def set_power(self, on: bool):
        """Allume ou éteint l'affichage."""
        if not self.is_connected:
            return
        print(f"[BLE] Demande d'alimentation : {'ON' if on else 'OFF'}")
        try:
            await self.client.send_command(TurnOnOffApp(on=on))
        except TimeoutError:
            print("[BLE] ⚠️ Avertissement : Pas d'accusé de réception pour l'alimentation (ignoré).")

    async def set_brightness(self, level: int):
        """Règle la luminosité de 0 (min) à 255 (max)."""
        if not self.is_connected:
            return
        level = max(0, min(255, level))
        print(f"[BLE] Réglage luminosité à {level}/255")
        try:
            await self.client.send_command(SetBrightness(brightness=level))
        except TimeoutError:
            print("[BLE] ⚠️ Avertissement : Pas d'accusé de réception pour la luminosité (ignoré).")

    def _buffer_to_image(self) -> Image.Image:
        image = Image.new("RGB", (self.width, self.height), (0, 0, 0))
        for y, row in enumerate(self.buffer):
            for x, color in enumerate(row):
                image.putpixel((x, y), color)
        return image

    async def show(self):
        if not self.is_connected:
            print("[WARN] Impossible d'afficher : matrice non connectée.")
            return

        temp_path = None
        try:
            image = self._buffer_to_image()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                temp_path = temp_file.name
                
            image.save(temp_path)
            
            cmd = SetImage(filename=temp_path)
            await self.client.send_command(cmd)
            
        except TimeoutError:
            print("[BLE] ⚠️ Avertissement : Timeout partiel sur l'envoi d'image (trame probablement reçue).")
        except Exception as e:
            print(f"[BLE] Erreur de transmission : {e}")
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
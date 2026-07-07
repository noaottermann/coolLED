import asyncio
from typing import Tuple
from coolledx import CoolLEDDevice 

class MatrixDisplay:
    def __init__(self, mac_address: str = "FF:00:00:04:1B:DF", width: int = 64, height: int = 16):
        self.mac_address = mac_address
        self.width = width
        self.height = height
        self.device = None
        self.is_connected = False
        
        self.buffer = [[(0, 0, 0) for _ in range(self.width)] for _ in range(self.height)]

    async def connect(self) -> bool:
        """Gère la connexion initiale à la matrice LED."""
        try:
            print(f"[BLE] Connexion à la matrice {self.mac_address}...")
            # Adaptation selon l'API exacte du fork de coolledx
            self.device = CoolLEDDevice(self.mac_address)
            await self.device.connect()
            self.is_connected = True
            print("[BLE] Connecté avec succès !")
            return True
        except Exception as e:
            print(f"[BLE] Erreur de connexion : {e}")
            self.is_connected = False
            return False

    async def disconnect(self):
        """Déconnexion propre de l'appareil."""
        if self.device and self.is_connected:
            await self.device.disconnect()
            self.is_connected = False
            print("[BLE] Déconnecté.")

    def set_pixel(self, x: int, y: int, color: Tuple[int, int, int]):
        """Modifie la couleur d'un pixel dans le buffer (sans envoyer au BLE immédiatement)."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.buffer[y][x] = color

    def fill(self, color: Tuple[int, int, int]):
        """Remplit tout le buffer avec une couleur unie."""
        self.buffer = [[color for _ in range(self.width)] for _ in range(self.height)]

    def clear(self):
        """Éteint tous les pixels dans le buffer."""
        self.fill((0, 0, 0))

    async def show(self):
        """Envoie le buffer actuel à la matrice physique via coolledx."""
        if not self.is_connected or not self.device:
            print("[WARN] Impossible d'afficher : non connecté.")
            return

        try:
            flat_pixels = [pixel for row in self.buffer for pixel in row]
            await self.device.show_image(flat_pixels) 
            
        except Exception as e:
            print(f"[BLE] Erreur lors de l'envoi des données : {e}")
            # Optionnel : tenter une reconnexion automatique ici
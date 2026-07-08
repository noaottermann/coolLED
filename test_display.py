"""Manual display test for the CoolLED matrix."""

import asyncio

from core.display import MatrixDisplay
from utils.config import DISPLAY_HEIGHT, DISPLAY_WIDTH, MAC_ADDRESS

async def main():
    matrix = MatrixDisplay(mac_address=MAC_ADDRESS, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT)
    
    if not await matrix.connect():
        print("❌ Impossible de se connecter.")
        return

    try:
        await matrix.set_power(True)
        await matrix.set_brightness(128)

        matrix.clear()
        for x in range(matrix.width):
            matrix.set_pixel(x, matrix.height // 2, (255, 0, 0))
        for y in range(matrix.height):
            matrix.set_pixel(matrix.width // 2, y, (0, 255, 0))
        matrix.set_pixel(matrix.width // 2, matrix.height // 2, (255, 255, 255))

        await matrix.show()
    except Exception as e:
        print(f"Erreur pendant le run : {e}")
    finally:
        await matrix.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import asyncio
from core.display import MatrixDisplay

async def main():
    # Instanciation du wrapper (Ajuste width/height si ta matrice fait 32x32 ou autre)
    matrix = MatrixDisplay(mac_address="FF:00:00:04:1B:DF", width=16, height=16)
    
    if await matrix.connect():
        # 1. Allumer un pixel de test en Rouge au milieu de l'écran
        matrix.set_pixel(8, 8, (255, 0, 0))
        await matrix.show()
        await asyncio.sleep(2)
        
        # 2. Remplir l'écran en Bleu
        matrix.fill((0, 0, 255))
        await matrix.show()
        await asyncio.sleep(2)
        
        # 3. Éteindre
        matrix.clear()
        await matrix.show()
        
        await matrix.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
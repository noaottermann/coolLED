import asyncio
from core.display import MatrixDisplay
from coolledx.commands import Initialize, SetText

async def main():
    matrix = MatrixDisplay(mac_address="FF:00:00:04:1B:DF", width=64, height=16)
    
    if not await matrix.connect():
        print("❌ Impossible de se connecter.")
        return

    try:
        print(f"🔍 Matériel auto-détecté par coolledx : {matrix.client.hardware.__class__.__name__}")

        # 2. INITIALISATION
        print("[BLE] Envoi de la commande d'initialisation...")
        try:
            await matrix.client.send_command(Initialize())
        except TimeoutError:
            print("[BLE] ⚠️ Pas d'ACK pour Initialize (ignoré, c'est normal).")
        await asyncio.sleep(1)

        # 3. ALIMENTATION ET LUMINOSITÉ
        await matrix.set_power(True)
        await asyncio.sleep(0.5)
        await matrix.set_brightness(255)
        await asyncio.sleep(0.5)

        # 4. LE TEST DU TEXTE
        print("📝 Test d'envoi de texte brut (HELLO)...")
        cmd_text = SetText(text="HELLO", default_color="red")
        await matrix.client.send_command(cmd_text)
        
        print("Trame texte envoyée ! Vérifiez l'écran.")
        await asyncio.sleep(5)
        
        # 5. LE TEST DE L'IMAGE
        print("💡 Tentative d'affichage des angles (Test Image)...")
        matrix.fill((0, 0, 0))
        matrix.set_pixel(0, 0, (255, 0, 0))          
        matrix.set_pixel(63, 0, (0, 255, 0))         
        matrix.set_pixel(0, 15, (0, 0, 255))         
        matrix.set_pixel(63, 15, (255, 255, 0))      
        await matrix.show()
        
        print("Trame image envoyée !")
        await asyncio.sleep(5)

    except Exception as e:
        print(f"Erreur pendant le run : {e}")
    finally:
        await matrix.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
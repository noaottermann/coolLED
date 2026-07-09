#!/usr/bin/env python3
"""
bluetooth_scanner.py
---------------------
Scanne les appareils Bluetooth LE à proximité (via Bleak) pour identifier
efficacement l'adresse MAC de ton écran CoolLEDM.

Deux modes :

1) Mode simple (par défaut) :
   Liste tous les appareils BLE détectés, triés par force de signal (RSSI),
   en mettant en évidence ceux dont le nom ressemble à "coolled"/"led".

       python bluetooth_scanner.py
       python bluetooth_scanner.py --duration 15

2) Mode différentiel (--diff) : LE PLUS FIABLE, même si l'appareil
   n'annonce aucun nom exploitable.
   Fait un premier scan (écran éteint), te demande d'allumer l'écran,
   puis fait un second scan et affiche uniquement les adresses NOUVELLES
   apparues entre les deux — donc quasi certainement ton écran.

       python bluetooth_scanner.py --diff

Prérequis : pip install bleak --break-system-packages (ou dans un venv)
"""

import argparse
import asyncio

from bleak import BleakScanner

KEYWORDS = ("coolled", "led", "juntong", "crosby")


def looks_like_led_device(name: str) -> bool:
    if not name:
        return False
    lname = name.lower()
    return any(k in lname for k in KEYWORDS)


def format_device_line(address, name, rssi, manufacturer_data=None, service_uuids=None):
    name_display = name if name else "(pas de nom annoncé)"
    line = f"  {address}   RSSI={rssi:>5} dBm   nom={name_display}"
    if manufacturer_data:
        md_str = ", ".join(
            f"0x{cid:04X}:{data.hex()}" for cid, data in manufacturer_data.items()
        )
        line += f"   manufacturer_data=[{md_str}]"
    if service_uuids:
        line += f"   service_uuids={service_uuids}"
    return line


async def scan_once(duration: float):
    """Retourne un dict {address: (name, rssi, manufacturer_data, service_uuids)}"""
    devices_and_adv = await BleakScanner.discover(timeout=duration, return_adv=True)
    result = {}
    for address, (device, adv) in devices_and_adv.items():
        result[address] = (
            adv.local_name or device.name,
            adv.rssi,
            dict(adv.manufacturer_data) if adv.manufacturer_data else {},
            list(adv.service_uuids) if adv.service_uuids else [],
        )
    return result


async def simple_scan(duration: float):
    print(f"[i] Scan en cours pendant {duration:.0f}s...\n")
    devices = await scan_once(duration)

    if not devices:
        print("[!] Aucun appareil BLE détecté. Vérifie que le Bluetooth du PC est actif "
              "et que l'écran est allumé et à proximité.")
        return

    # Tri : candidats "LED" en premier, puis par RSSI décroissant (signal le plus fort = le plus proche)
    def sort_key(item):
        address, (name, rssi, _, _) = item
        return (0 if looks_like_led_device(name) else 1, -rssi)

    sorted_devices = sorted(devices.items(), key=sort_key)

    candidates = [d for d in sorted_devices if looks_like_led_device(d[1][0])]
    others = [d for d in sorted_devices if not looks_like_led_device(d[1][0])]

    if candidates:
        print(f"[✓] {len(candidates)} candidat(s) probable(s) (nom évocateur) :")
        for address, (name, rssi, md, svc) in candidates:
            print(format_device_line(address, name, rssi, md, svc))
        print()
    else:
        print("[i] Aucun appareil n'annonce un nom évocateur (\"coolled\", \"led\", ...).\n"
              "    Passez au mode --diff pour une identification fiable.\n")

    print(f"[i] Tous les autres appareils détectés ({len(others)}), triés par signal :")
    for address, (name, rssi, md, svc) in others:
        print(format_device_line(address, name, rssi, md, svc))


async def diff_scan(duration: float):
    input("[1/2] Assure-toi que l'écran LED est ÉTEINT, puis appuie sur Entrée pour lancer "
          "le premier scan de référence...")
    print(f"[i] Scan de référence ({duration:.0f}s)...\n")
    before = await scan_once(duration)
    print(f"[i] {len(before)} appareil(s) détecté(s) avant allumage.\n")

    input("[2/2] Allume maintenant l'écran LED (et rapproche-le si besoin), "
          "puis appuie sur Entrée pour lancer le second scan...")
    print(f"[i] Second scan ({duration:.0f}s)...\n")
    after = await scan_once(duration)
    print(f"[i] {len(after)} appareil(s) détecté(s) après allumage.\n")

    new_addresses = set(after.keys()) - set(before.keys())

    if not new_addresses:
        print("[!] Aucune nouvelle adresse détectée entre les deux scans.\n"
              "    Essayez d'augmenter --duration, de rapprocher l'écran, ou de bien vérifier\n"
              "    qu'il était éteint pendant le premier scan.")
        return

    print(f"[✓] {len(new_addresses)} nouvelle(s) adresse(s) apparue(s) après allumage "
          f"— candidat(s) très probable(s) :")
    for address in new_addresses:
        name, rssi, md, svc = after[address]
        print(format_device_line(address, name, rssi, md, svc))


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--duration", type=float, default=10.0,
                         help="durée de chaque scan en secondes (défaut: 10)")
    parser.add_argument("--diff", action="store_true",
                         help="mode différentiel (avant/après allumage), le plus fiable")
    args = parser.parse_args()

    if args.diff:
        asyncio.run(diff_scan(args.duration))
    else:
        asyncio.run(simple_scan(args.duration))


if __name__ == "__main__":
    main()
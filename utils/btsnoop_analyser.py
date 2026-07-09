#!/usr/bin/env python3
"""
parse_btsnoop.py
-----------------
Analyseur "mini-Wireshark" pour fichiers btsnoop_hci.log (export Android,
via bug report), écrit en pur Python standard (aucune dépendance externe,
donc pas besoin de pip install / droits admin).

Objectif : isoler les échanges BLE ATT (Write Request / Write Command /
Notification / Indication) avec un appareil cible (ex: ton écran CoolLEDM),
pour faciliter le reverse engineering du protocole.

Usage :
    python parse_btsnoop.py btsnoop_hci.log
    python parse_btsnoop.py btsnoop_hci.log --mac FF:00:00:04:1B:DF
    python parse_btsnoop.py btsnoop_hci.log --mac FF:00:00:04:1B:DF --out capture1.txt

Sans --mac, le script liste toutes les adresses BLE vues dans la capture
(via les événements de connexion), pour t'aider à identifier la bonne.
"""

import struct
import sys
import argparse

# Constantes du format btsnoop
BTSNOOP_MAGIC = b"btsnoop\x00"
HEADER_LEN = 16  # magic(8) + version(4) + datalink(4)
RECORD_HEADER_LEN = 24  # orig_len(4) incl_len(4) flags(4) drops(4) ts(8)

# Types de paquets H4 (utilisés quand datalink == 1002)
H4_CMD = 0x01
H4_ACL = 0x02
H4_SCO = 0x03
H4_EVT = 0x04

# Event codes HCI intéressants
HCI_EVT_LE_META = 0x3E
LE_SUBEVT_CONN_COMPLETE = 0x01
LE_SUBEVT_ENH_CONN_COMPLETE = 0x0A

ATT_CID = 0x0004  # canal fixe ATT en BLE

ATT_OPCODES = {
    0x01: "Error Response",
    0x02: "Exchange MTU Request",
    0x03: "Exchange MTU Response",
    0x04: "Find Information Request",
    0x05: "Find Information Response",
    0x06: "Find By Type Value Request",
    0x07: "Find By Type Value Response",
    0x08: "Read By Type Request",
    0x09: "Read By Type Response",
    0x0A: "Read Request",
    0x0B: "Read Response",
    0x0C: "Read Blob Request",
    0x0D: "Read Blob Response",
    0x0E: "Read Multiple Request",
    0x0F: "Read Multiple Response",
    0x10: "Read By Group Type Request",
    0x11: "Read By Group Type Response",
    0x12: "Write Request",
    0x13: "Write Response",
    0x16: "Prepare Write Request",
    0x17: "Prepare Write Response",
    0x18: "Execute Write Request",
    0x19: "Execute Write Response",
    0x1B: "Handle Value Notification",
    0x1D: "Handle Value Indication",
    0x1E: "Handle Value Confirmation",
    0x52: "Write Command",
    0xD2: "Signed Write Command",
}

# Opcodes qui nous intéressent vraiment pour le reverse engineering
INTERESTING_OPCODES = {0x12, 0x52, 0x1B, 0x1D, 0x0B, 0x13}


def mac_str(addr_bytes):
    """Les adresses BLE sont stockées little-endian dans les événements HCI."""
    return ":".join("{:02X}".format(b) for b in reversed(addr_bytes))


def parse_btsnoop(path):
    with open(path, "rb") as f:
        data = f.read()

    if data[:8] != BTSNOOP_MAGIC:
        raise ValueError("Ce fichier ne semble pas être un btsnoop_hci.log valide "
                          "(magic bytes incorrects).")

    version, datalink = struct.unpack(">II", data[8:HEADER_LEN])
    if datalink != 1002:
        print(f"[!] Attention : datalink type = {datalink} (1002 = H4 attendu). "
              f"Le parsing pourrait être incorrect.", file=sys.stderr)

    offset = HEADER_LEN
    records = []
    while offset + RECORD_HEADER_LEN <= len(data):
        orig_len, incl_len, flags, drops, ts = struct.unpack(
            ">IIIIq", data[offset:offset + RECORD_HEADER_LEN]
        )
        offset += RECORD_HEADER_LEN
        packet = data[offset:offset + incl_len]
        offset += incl_len

        direction = "RECV" if (flags & 0x01) else "SENT"
        records.append((ts, direction, packet))

    return records


def extract_handle_to_mac(records):
    """Parcourt les événements LE Connection Complete pour mapper
    connection_handle -> adresse MAC BLE."""
    handle_map = {}

    for ts, direction, packet in records:
        if not packet or packet[0] != H4_EVT:
            continue
        body = packet[1:]
        if len(body) < 2:
            continue
        evt_code, param_len = body[0], body[1]
        params = body[2:2 + param_len]

        if evt_code != HCI_EVT_LE_META or len(params) < 1:
            continue

        subevent = params[0]

        if subevent == LE_SUBEVT_CONN_COMPLETE and len(params) >= 13:
            # status(1) handle(2) role(1) peer_addr_type(1) peer_addr(6) ...
            handle = struct.unpack("<H", params[2:4])[0]
            addr = params[6:12]
            handle_map[handle] = mac_str(addr)

        elif subevent == LE_SUBEVT_ENH_CONN_COMPLETE and len(params) >= 19:
            handle = struct.unpack("<H", params[2:4])[0]
            addr = params[6:12]
            handle_map[handle] = mac_str(addr)

    return handle_map


def iter_att_packets(records):
    """Génère (timestamp, direction, conn_handle, att_opcode, att_payload)
    pour chaque paquet ACL contenant une trame ATT."""
    for ts, direction, packet in records:
        if not packet or packet[0] != H4_ACL:
            continue
        body = packet[1:]
        if len(body) < 8:
            continue

        handle_flags = struct.unpack("<H", body[0:2])[0]
        conn_handle = handle_flags & 0x0FFF
        acl_len = struct.unpack("<H", body[2:4])[0]
        l2cap_payload = body[4:4 + acl_len]

        if len(l2cap_payload) < 4:
            continue

        l2cap_len = struct.unpack("<H", l2cap_payload[0:2])[0]
        cid = struct.unpack("<H", l2cap_payload[2:4])[0]

        if cid != ATT_CID:
            continue

        att_data = l2cap_payload[4:4 + l2cap_len]
        if not att_data:
            continue

        opcode = att_data[0]
        payload = att_data[1:]
        yield ts, direction, conn_handle, opcode, payload


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("logfile", help="chemin vers btsnoop_hci.log")
    parser.add_argument("--mac", help="adresse MAC à filtrer (ex: FF:00:00:04:1B:DF). "
                                       "Si omis, liste toutes les adresses trouvées.")
    parser.add_argument("--out", help="fichier de sortie texte (en plus de l'affichage console)")
    parser.add_argument("--all-opcodes", action="store_true",
                         help="afficher tous les opcodes ATT, pas seulement Write/Notify")
    args = parser.parse_args()

    records = parse_btsnoop(args.logfile)
    print(f"[i] {len(records)} paquets HCI lus depuis {args.logfile}")

    handle_map = extract_handle_to_mac(records)
    if not args.mac:
        print("\n[i] Adresses BLE détectées dans la capture (connexions établies) :")
        if not handle_map:
            print("    Aucune trouvée. Vérifie que l'appareil s'est bien (re)connecté "
                  "PENDANT la capture (débranche/rebranche le Bluetooth avant de lancer l'appli).")
        for h, m in handle_map.items():
            print(f"    handle={h}  ->  {m}")
        print("\nRelance avec --mac <adresse> pour filtrer et voir le détail des trames.")
        return

    target_mac = args.mac.upper()
    target_handles = {h for h, m in handle_map.items() if m == target_mac}
    if not target_handles:
        print(f"[!] Aucun connection handle trouvé pour {target_mac} dans cette capture.")
        print("    Adresses disponibles :", list(handle_map.values()))
        return

    out_lines = []
    count = 0
    t0 = records[0][0] if records else 0

    for ts, direction, conn_handle, opcode, payload in iter_att_packets(records):
        if conn_handle not in target_handles:
            continue
        if not args.all_opcodes and opcode not in INTERESTING_OPCODES:
            continue

        count += 1
        rel_ms = (ts - t0) / 1000.0
        opname = ATT_OPCODES.get(opcode, f"Opcode 0x{opcode:02X}")
        hex_payload = payload.hex()

        # Pour Write Request/Command, les 2 premiers octets du payload
        # sont l'attribute handle (little-endian), le reste est la vraie donnée envoyée
        if opcode in (0x12, 0x52) and len(payload) >= 2:
            att_handle = struct.unpack("<H", payload[0:2])[0]
            data = payload[2:]
            line = (f"[{rel_ms:9.2f} ms] {direction:4s} {opname:28s} "
                    f"attr_handle=0x{att_handle:04X}  data={data.hex()}")
        else:
            line = (f"[{rel_ms:9.2f} ms] {direction:4s} {opname:28s} "
                    f"raw_payload={hex_payload}")

        print(line)
        out_lines.append(line)

    print(f"\n[i] {count} trames ATT pertinentes affichées pour {target_mac}.")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write("\n".join(out_lines) + "\n")
        print(f"[i] Résultat également écrit dans {args.out}")


if __name__ == "__main__":
    main()
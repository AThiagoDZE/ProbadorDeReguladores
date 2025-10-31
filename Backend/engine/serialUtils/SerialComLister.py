#!/usr/bin/env python3
"""
find_board.py
Escanea puertos serie y dispositivos USB, imprime propiedades y permite
buscar una placa por VID+PID o por serial_number.

Uso:
    python find_board.py                # lista puertos y USB
    python find_board.py --vid 0x1A86 --pid 0x7523  # busca por VID/PID
    python find_board.py --serial ABC123   # busca por serial (recomendado)
    python find_board.py --watch --serial ABC123  # se queda viendo y reporta cambios
"""
import time
import argparse

from serial.tools import list_ports

# Intentaremos importar pyusb para más info USB (opcional)
try:
    import usb.core
    import usb.util
    HAS_PYUSB = True
except Exception:
    HAS_PYUSB = False

def list_serial_ports():
    """Lista puertos serie (pyserial) con propiedades útiles."""
    ports = list_ports.comports()
    out = []
    for p in ports:
        info = {
            "device": p.device,                # ej. /dev/ttyUSB0 o COM3
            "name": p.name,
            "description": p.description,
            "hwid": p.hwid,
            "vid": hex(p.vid) if p.vid is not None else None,
            "pid": hex(p.pid) if p.pid is not None else None,
            "serial_number": p.serial_number,
            "manufacturer": p.manufacturer,
            "product": p.product,
            "interface": getattr(p, "interface", None),
        }
        out.append(info)
    return out

def list_usb_devices():
    """Lista dispositivos USB usando pyusb (si está disponible)."""
    if not HAS_PYUSB:
        return None
    devices = []
    for dev in usb.core.find(find_all=True):
        try:
            vid = dev.idVendor
            pid = dev.idProduct
            # intento de leer strings (puede fallar si permisos insuficientes)
            manufacturer = usb.util.get_string(dev, dev.iManufacturer) if dev.iManufacturer else None
            product = usb.util.get_string(dev, dev.iProduct) if dev.iProduct else None
            serial = usb.util.get_string(dev, dev.iSerialNumber) if dev.iSerialNumber else None
        except Exception:
            manufacturer = product = serial = None
        devices.append({
            "bus": dev.bus if hasattr(dev, "bus") else None,
            "address": dev.address if hasattr(dev, "address") else None,
            "vid": hex(vid),
            "pid": hex(pid),
            "manufacturer": manufacturer,
            "product": product,
            "serial": serial,
        })
    return devices

def pretty_print_ports(ports):
    if not ports:
        print("No se encontraron puertos serie.")
        return
    for p in ports:
        print("----")
        for k,v in p.items():
            print(f"{k:14}: {v}")
    print("----")

def pretty_print_usb(devs):
    if devs is None:
        print("(pyusb no instalado o no disponible; saltando listado USB puro.)")
        return
    if not devs:
        print("No se encontraron dispositivos USB.")
        return
    for d in devs:
        print("----")
        for k,v in d.items():
            print(f"{k:12}: {v}")
    print("----")

def match_board(ports, vid=None, pid=None, serial=None):
    """Busca coincidencias en la lista de puertos. Retorna lista de matches."""
    matches = []
    for p in ports:
        p_vid = p.get("vid")
        p_pid = p.get("pid")
        p_serial = p.get("serial_number")
        if serial:
            if p_serial and serial in p_serial:
                matches.append(p)
        else:
            # comparar vid/pid si se pasaron
            match_vid = (vid is None) or (p_vid and p_vid.lower() == vid.lower())
            match_pid = (pid is None) or (p_pid and p_pid.lower() == pid.lower())
            if match_vid and match_pid:
                matches.append(p)
    return matches

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vid", help="Vendor ID hex, e.g. 0x1A86")
    parser.add_argument("--pid", help="Product ID hex, e.g. 0x7523")
    parser.add_argument("--serial", help="Serial number (substring allowed)")
    parser.add_argument("--watch", action="store_true", help="Queda observando cambios y reporta cuando aparece/desaparece")
    parser.add_argument("--interval", type=float, default=2.0, help="Intervalo watch en segundos")
    args = parser.parse_args()

    def scan_once():
        ports = list_serial_ports()
        usb = list_usb_devices()
        print("\n=== Puertos serie encontrados ===")
        pretty_print_ports(ports)
        print("\n=== Dispositivos USB (pyusb) ===")
        pretty_print_usb(usb)
        if args.vid or args.pid or args.serial:
            # normalizar hex para comparar
            vid_norm = args.vid.lower() if args.vid else None
            pid_norm = args.pid.lower() if args.pid else None
            matches = match_board(ports, vid=vid_norm, pid=pid_norm, serial=args.serial)
            if matches:
                print("\n>>> MATCH(es) encontrados:")
                pretty_print_ports(matches)
            else:
                print("\n>>> No se encontró la placa buscada.")
        return ports

    if not args.watch:
        scan_once()
        return

    # modo watch: detectar apariciones/desapariciones
    previous = {}
    try:
        while True:
            ports = list_serial_ports()
            # construir set de device names
            current_map = {p["device"]: p for p in ports}
            # detect added
            added = [p for dev,p in current_map.items() if dev not in previous]
            removed = [p for dev,p in previous.items() if dev not in current_map]
            if added:
                print(f"\n[+] Añadidos ({len(added)}):")
                pretty_print_ports(added)
            if removed:
                print(f"\n[-] Retirados ({len(removed)}):")
                pretty_print_ports(removed)
            # si se busca una placa específica, avisar si aparece
            if args.vid or args.pid or args.serial:
                vid_norm = args.vid.lower() if args.vid else None
                pid_norm = args.pid.lower() if args.pid else None
                matches = match_board(ports, vid=vid_norm, pid=pid_norm, serial=args.serial)
                if matches:
                    print("\n>>> Placa objetivo DETECTADA:")
                    pretty_print_ports(matches)
            previous = current_map
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nObservación interrumpida por usuario. Saliendo.")

if __name__ == "__main__":
    main()

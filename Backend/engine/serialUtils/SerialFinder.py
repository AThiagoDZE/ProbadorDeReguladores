from serial.tools import list_ports

TARGET_VID = "0483"  # solo números hex
TARGET_PID = "374B"  # solo números hex
TARGET_SERIAL = "066DFF313358353143085514"

def normalize_hex(value):
    """Convierte a string hex sin 0x y en mayúsculas."""
    if value is None:
        return None
    return format(value, '04X')

def find_stlink():
    ports = list_ports.comports()
    for p in ports:
        vid = normalize_hex(p.vid)
        pid = normalize_hex(p.pid)
        serial = p.serial_number.strip() if p.serial_number else None
        if vid == TARGET_VID and pid == TARGET_PID and serial == TARGET_SERIAL:
            print(f"Placa encontrada en: {p.device}")
            return True, p.device
    return False, None

if __name__ == "__main__":
    com_port = find_stlink()
    if com_port:
        print(f"Placa encontrada en: {com_port}")
    else:
        print("Placa no encontrada")

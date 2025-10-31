import serial
import threading
import time
from typing import Optional, Callable
import random

class SerialHandler:
    def __init__(self, port: str, baudrate: int, callback: Optional[Callable[[str, bool], None]] = None):
        self.port = port
        self.baudrate = baudrate
        # Callback por defecto: imprime con prefijo según incoming
        if callback is None:
            self.callback: Callable[[str, bool], None] = lambda msg, incoming=True: \
                print(f"{'<-' if incoming else '->'} {msg}")
        else:
            self.callback = callback

        self.ser: Optional[serial.Serial] = None
        self.running = False

        self._recv_thread = threading.Thread(target=self._recv_loop)
        self._recv_thread.daemon = True

    def start(self):
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            self.running = True
            self._recv_thread.start()
            self._log(f"Puerto serie {self.port} abierto a {self.baudrate} bps")
        except serial.SerialException as e:
            self._log(f"No se pudo abrir el puerto serie ({self.port}). Modo simulado activado. Detalle: {e}")
            self.ser = None
            self.running = True
            self._recv_thread.start()

    def stop(self):
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
            self._log("Puerto serie cerrado")

    def send(self, cmd_bytes: bytes, description: str = ""):
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(cmd_bytes)
                self._log(f"TX: {cmd_bytes.hex()} ({description})", incoming=False)
            except serial.SerialException as e:
                self._log(f"Error enviando datos: {e}", incoming=False)
        else:
            # Modo simulado: loguea el envío
            self._log(f"[SIMULADO] TX: {cmd_bytes.hex()} ({description})", incoming=False)
            # opcional: generar respuesta simulada
            if random.random() < 0.5:
                self._log(f"[SIMULADO] RX: {cmd_bytes.hex()}_RESPUESTA", incoming=True)

    def _recv_loop(self):
        while self.running:
            try:
                if self.ser and self.ser.in_waiting > 0:
                    data = self.ser.read(self.ser.in_waiting)
                    self._log(f"RX: {data.hex()}", incoming=True)
            except serial.SerialException as e:
                self._log(f"Error leyendo datos: {e}", incoming=True)
                break
            time.sleep(0.05)

    def _log(self, message: str, incoming: bool = True):
        timestamp = time.strftime("%H:%M:%S")
        self.callback(f"[{timestamp}] {message}", incoming=incoming)


# --- Uso completo de ejemplo ---
if __name__ == "__main__":
    def print_callback(msg: str, incoming: bool):
        prefix = "<-" if incoming else "->"
        print(f"{prefix} {msg}")

    # Crear handler
    sh = SerialHandler("COM9", 115200, callback=print_callback)

    # Iniciar puerto serie (o simulación si no hay hardware)
    sh.start()
    time.sleep(1)

    # Enviar varios comandos
    for i in range(3):
        cmd = f"A9040070110019{i:02X}"  # ejemplo hexadecimal
        sh.send(bytes.fromhex(cmd), f"Comando de prueba {i+1}")
        time.sleep(1)

    # Mantener el programa activo para que _recv_loop reciba datos
    print("Esperando datos... (simulados si no hay puerto)")
    for _ in range(5):
        time.sleep(1)

    # Detener puerto serie
    sh.stop()
    print("Programa finalizado.")

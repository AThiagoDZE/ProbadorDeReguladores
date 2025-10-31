import struct
import time
import threading
import serial
import numpy as np



class DZETester:
    """
    Módulo de comunicación para el Probador de Reguladores DZE.
    Permite manejar toda la comunicación serie, procesar respuestas
    y obtener valores de tensión, corriente y estado del equipo.
    """

    def __init__(self, port="COM5", baudrate=1843200, callback=None, debug=False):
        self.port = port
        self.baudrate = baudrate
        self.callback = callback
        self.debug = debug

        self.ser = None
        self.running = False
        self.condition = threading.Condition()

        self.TensionSalida = 0.0
        self.CorrienteCarga = 0.0
        self.CorrienteEnsayo = 0.0
        self.RPM = 0.0
        self.RMS = 0.0
        self.msg_gui = ""
        self.lecturas = []  # almacena lecturas recibidas [(tipo, valor, timestamp), ...]

        # Hilos
        self.thread_recv = threading.Thread(target=self._recibir_datos, daemon=True)
        self.thread_keepalive = threading.Thread(target=self._keep_alive, daemon=True)

    # ----------------------------------------------------------------------
    # CONTROL DE COMUNICACIÓN
    # ----------------------------------------------------------------------

    def start(self):
        """Inicia la comunicación serie y los hilos de recepción."""
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(1)
            self.running = True
            self._log(f"Puerto {self.port} abierto a {self.baudrate} bps.")

            self._configurar_placa()
            self.thread_recv.start()
            self.thread_keepalive.start()

        except serial.SerialException as e:
            self._log(f"❌ Error abriendo puerto serie: {e}")
            self.running = False

    def stop(self):
        """Detiene la comunicación."""
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
        self._log("Conexión cerrada.")

    def _log(self, msg):
        if self.debug:
            print(msg)

    # ----------------------------------------------------------------------
    # ENVÍO DE COMANDOS
    # ----------------------------------------------------------------------

    def _send(self, cmd, desc=""):
        """Envía un comando en formato hexadecimal."""
        if not self.ser or not self.ser.is_open:
            self._log("❌ Puerto no abierto.")
            return

        try:
            self.ser.flush()
            self.ser.write(bytes.fromhex(cmd[0:8]))
            time.sleep(0.002)
            if len(cmd) > 8:
                self.ser.write(bytes.fromhex(cmd[8:]))
            self._log(f"➡️ TX [{desc}] ({cmd})")
        except serial.SerialException as e:
            self._log(f"Error al enviar datos: {e}")

    def _configurar_placa(self):
        """Configura la placa al iniciar la conexión."""
        comandos = [
            "85FFFFBF", "05C30082", "06000060", "06000060",
            "4900007010002800", "4900007010002000", "4900007010006000",
            "4900007011006900", "490000701100A900", "490000701100E900",
            "490000701100A100", "490000701100E100", "4900007011002901",
            "4900007011002902",
            "D900004008002905070000040000FF0000",
        ]

        for c in comandos:
            self._send(c, "Config inicial")
            time.sleep(0.1)
        self._log("✅ Placa configurada y conectada.")
        self.msg_gui = "Placa configurada."

    # ----------------------------------------------------------------------
    # BUCLE KEEP-ALIVE
    # ----------------------------------------------------------------------

    def _keep_alive(self):
        """Envía periódicamente un mensaje de estado."""
        time.sleep(2)
        mensaje = (
            "A9040070110019005900591B9900D90019019102D10251099101D101911451149100D1009109D1081109D105910551039103910451041119D118910B510BD10B110C510C910CD11A49008900C900"
        )
        while self.running:
            self._send(mensaje, "KeepAlive")
            time.sleep(0.2)

    # ----------------------------------------------------------------------
    # RECEPCIÓN Y PARSEO
    # ----------------------------------------------------------------------

    def _recibir_datos(self):
        """Procesa los datos que llegan del puerto serie."""
        while self.running:
            try:
                if self.ser.in_waiting:
                    data = self.ser.read(self.ser.in_waiting)
                    hex_data = data.hex()
                    self._parse_data(hex_data)
            except serial.SerialException as e:
                self._log(f"❌ Error recibiendo datos: {e}")
                break
            time.sleep(0.05)

    def _parse_data(self, hex_data):
        """Interpreta los mensajes recibidos según el protocolo."""
        if hex_data == "1a00002000":
            self._notify("ack", "Comando recibido OK")

        elif hex_data.startswith("2a050040"):
            # Tensión
            byte_data = bytes.fromhex(hex_data[88:92])
            tension_mV = struct.unpack("<h", byte_data)[0]
            self.TensionSalida = round(tension_mV / 1000.0, 3)
            self._store("tension", self.TensionSalida)

        elif hex_data.startswith("e93f00b0"):
            # RMS
            hex_str = hex_data[16:]
            if len(hex_str) % 4 != 0:
                return
            vals = [struct.unpack("<h", bytes.fromhex(hex_str[i:i+4]))[0]
                    for i in range(0, len(hex_str), 4)]
            self.RMS = round(float(np.sqrt(np.mean(np.square(vals)))), 3)
            self._store("rms", self.RMS)

    def _store(self, tipo, valor):
        """Guarda y notifica una nueva lectura."""
        ts = time.time()
        self.lecturas.append((tipo, valor, ts))
        self._notify(tipo, valor)
        self._log(f"RX {tipo}: {valor}")

    def _notify(self, tipo, valor):
        """Llama al callback externo si existe."""
        if self.callback:
            try:
                self.callback(tipo, valor)
            except Exception as e:
                self._log(f"Error en callback: {e}")

    # ----------------------------------------------------------------------
    # COMANDOS DE ENSAYO
    # ----------------------------------------------------------------------

    def set_corriente_carga(self, mA):
        """Configura corriente de carga (mA)."""
        self.CorrienteCarga = mA / 1000.0
        base = "6900000008009100"
        payload = struct.pack("<h", mA).hex()
        self._send(base + payload, f"Set corriente carga {mA}mA")

    def set_corriente_prueba(self, mA):
        """Configura corriente de ensayo para regulador paralelo."""
        self.CorrienteEnsayo = mA / 1000.0
        val = int(mA / 0.0006715014773 / 1000)
        base = "6900000008009109"
        payload = struct.pack("<h", val).hex()
        self._send(base + payload, f"Set corriente ensayo {mA}mA")

    def probar_regulador_paralelo(self):
        """Ejecuta el ciclo completo de prueba del regulador paralelo."""
        self._log("--- PROBANDO REGULADOR PARALELO ---")
        self._send("290000E03900", "ACK Error previo")
        self._send("590000F00800890002", "Modo paralelo")

        for mA in range(0, 401, 50):
            self.set_corriente_carga(mA)
            time.sleep(0.05)

        self._send("290000E01900", "Comando Start")

        for mA in range(0, 1201, 100):
            self.set_corriente_prueba(mA)
            time.sleep(0.05)

        self._send("F9000030080029050900FE030001FF00D10711", "Datos Ia")
        time.sleep(10)
        self._send("290000E02100", "Comando Stop")

    # ----------------------------------------------------------------------
    # OBTENCIÓN DE DATOS
    # ----------------------------------------------------------------------

    def get_estado(self):
        """Devuelve el último estado medido en un dict."""
        return {
            "tension": self.TensionSalida,
            "corriente_carga": self.CorrienteCarga,
            "corriente_ensayo": self.CorrienteEnsayo,
            "rms": self.RMS,
            "rpm": self.RPM,
            "timestamp": time.time(),
        }


# ----------------------------------------------------------------------
# EJEMPLO DE USO
# ----------------------------------------------------------------------

if __name__ == "__main__":

    def imprimir_datos(tipo, valor):
        print(f"[CALLBACK] {tipo}: {valor}")

    tester = DZETester(port="COM5", debug=True, callback=imprimir_datos)
    tester.start()

    time.sleep(3)
    tester.probar_regulador_paralelo()

    time.sleep(5)
    print("Último estado:", tester.get_estado())
    tester.stop()

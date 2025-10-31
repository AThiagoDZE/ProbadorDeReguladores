import struct
import time
import threading
import serial
import numpy as np

COLOR_AZUL = '\033[94m'
COLOR_ROJO = '\033[91m'
COLOR_VERDE = '\033[93m'
COLOR_MAGENTA = '\033[95m'
COLOR_RESET = '\033[0m'

PUERTO_SERIE = 'COM5'
BAUD_RATE = 1843200


class DZETester:
    def __init__(self, callback=None):
        self.callback = callback
        self.running = False
        self.condition = threading.Condition()

        self.hilo_enviar = threading.Thread(target=self.keep_alive_status)
        self.hilo_recibir = threading.Thread(target=self.recibir_datos)

        self.hilo_enviar.daemon = True
        self.hilo_recibir.daemon = True

        self.TensionSalida = 0.0
        self.CorrienteCarga = 0.0
        self.CorrienteEnsayo = 0.0
        self.RPM = 800
        self.CorrienteFlux = 0.0
        self.msg_gui = ""

    def start(self):
        try:
            self.ser = serial.Serial(PUERTO_SERIE, BAUD_RATE, timeout=2)
            time.sleep(1)
            print(f"Puerto serie {PUERTO_SERIE} abierto a {BAUD_RATE} bps.")
            self.hilo_recibir.start()
            self.running = True
            self.configurar_placa()
            self.hilo_enviar.start()
        except serial.SerialException as e:
            print(f"Error abriendo puerto serie: {e}")
            self.ser = None

    def stop(self):
        self.running = False

    def send(self, cmd, description=""):
        try:
            self.ser.flush()
            self.ser.write(bytes.fromhex(cmd[0:8]))
            time.sleep(0.002)
            self.ser.write(bytes.fromhex(cmd[8:]))
            print(f"{COLOR_AZUL}TX: {description} : ({cmd}){COLOR_RESET}")
        except serial.SerialException as e:
            print(f"Error al enviar datos: {e}")
        time.sleep(0.1)

    def configurar_placa(self):
        mensajes = [
            "85FFFFBF",
            "05C30082",
            "06000060",
            "06000060",
            "4900007010002800",
            "4900007010002000",
            "4900007010006000",
            "4900007011006900",
            "490000701100A900",
            "490000701100E900",
            "490000701100A100",
            "490000701100E100",
            "4900007011002901",
            "4900007011002902",
            "D900004008002905070000040000FF0000",
        ]

        with self.condition:
            for msg in mensajes:
                try:
                    self.ser.flush()
                    self.ser.write(bytes.fromhex(msg[0:8]))
                    time.sleep(0.002)
                    self.ser.write(bytes.fromhex(msg[8:]))
                    print(f"{COLOR_AZUL}Enviado: {msg}{COLOR_RESET}")
                except serial.SerialException as e:
                    print(f"Error al enviar datos: {e}")
                    break
                time.sleep(0.1)
            print(f"{COLOR_AZUL}Enviado: PLACA CONECTADA {COLOR_RESET}")
            self.msg_gui = "Placa configurada y conectada."
            self.condition.notify_all()

    def keep_alive_status(self):
        time.sleep(2)
        mensaje = (
            "A9040070110019005900591B9900D90019019102D10251099101D101911451149100D1009109D1081109D105910551039103910451041119D118910B510BD10B110C510C910CD11A49008900C900"
        )
        with self.condition:
            while True:
                self.send(mensaje, "Lectura status")
                time.sleep(0.2)

    def SetearCorrienteCarga(self, corriente):
        self.CorrienteCarga = corriente / 1000.0
        mensaje_base = "6900000008009100"
        porcentaje_hex = struct.pack("<h", corriente).hex()
        msj = mensaje_base + porcentaje_hex
        print(f"{COLOR_MAGENTA}Seteando Corriente de Carga a {corriente} mA ({msj})")
        self.send(msj, f"Seteo Corriente de Carga a {corriente} mA")

    def SetearCorrientePruebaRegParalelo(self, corriente):
        self.CorrienteEnsayo = corriente / 1000.0
        corriente = int(corriente / 0.0006715014773 / 1000)
        mensaje_base = "6900000008009109"
        porcentaje_hex = struct.pack("<h", corriente).hex()
        msj = mensaje_base + porcentaje_hex
        self.send(msj, f"Seteo Corriente de ensayo a {corriente}")

    def recibir_datos(self):
        while True:
            try:
                if self.ser.in_waiting > 0:
                    datos_recibidos = self.ser.read(self.ser.in_waiting)
                    hex_representation = datos_recibidos.hex()

                    if hex_representation == "1a00002000":
                        print(f"{COLOR_ROJO}RX: Comando recibido OK! - ({hex_representation})")

                    elif hex_representation.startswith("2a050040"):
                        byte_data = bytes.fromhex(hex_representation[88:92])
                        tension_mV = struct.unpack("<h", byte_data)[0]
                        self.TensionSalida = tension_mV / 1000.0
                        print(f"{COLOR_ROJO}RX: TENSION {self.TensionSalida} - ({hex_representation})")

                    elif hex_representation.startswith("e93f00b0"):
                        hex_str = hex_representation[16:]
                        if len(hex_str) % 4 != 0:
                            raise ValueError("Hex string length must be a multiple of 4 for int16 values.")

                        chunks = [hex_str[i:i+4] for i in range(0, len(hex_str), 4)]
                        int16_array = []
                        for chunk in chunks:
                            byte_data = bytes.fromhex(chunk)
                            value = struct.unpack("<h", byte_data)[0]
                            int16_array.append(value)

                        rms = np.sqrt(np.mean(np.square(int16_array)))
                        print(f"{COLOR_VERDE}RMS: {rms}{COLOR_RESET}")

            except serial.SerialException as e:
                print(f"Error al recibir datos: {e}")
                break
            time.sleep(0.1)

    def ProbarReguladorSerie(self):
        print(f"{COLOR_VERDE}--- PROBANDO REGULADOR SERIE ---{COLOR_RESET}")
        self.msg_gui = "Iniciando prueba regulador serie..."
        self.send("590000F00800890002", "Configurar modo regulador serie")
        mensaje_base = "690000000800D11A"
        for porcentaje in range(0, 101, 5):
            porcentaje_hex = struct.pack("<h", porcentaje).hex()
            mensaje = mensaje_base + porcentaje_hex
            self.send(mensaje, f"Set porcentaje {porcentaje}")
            time.sleep(0.1)

    def ProbarReguladorParalelo(self):
        print(f"{COLOR_VERDE}--- PROBANDO REGULADOR PARALELO ---{COLOR_RESET}")
        self.msg_gui = "Iniciando prueba regulador paralelo..."
        self.send("290000E03900", "ACK Error previo")
        self.send("590000F00800890002", "Configurar modo regulador paralelo")

        for mA in range(0, 401, 50):
            self.SetearCorrienteCarga(mA)
            time.sleep(0.05)

        self.send("290000E01900", "Comando Start")

        for mA in range(0, 1201, 100):
            self.SetearCorrientePruebaRegParalelo(mA)
            time.sleep(0.05)

        self.send("F9000030080029050900FE030001FF00D10711", "Datos Ia")
        time.sleep(10)
        self.send("290000E02100", "Comando Stop")


if __name__ == "__main__":
    tester = DZETester()
    tester.start()
    time.sleep(3)
    tester.ProbarReguladorParalelo()

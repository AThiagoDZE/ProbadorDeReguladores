import struct
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
import asynckivy as ak
from kivy.properties import StringProperty, DictProperty
import time
import random
import threading
import serial
import asyncio

import numpy as np

COLOR_AZUL = '\033[94m'
COLOR_ROJO = '\033[91m'
COLOR_VERDE = '\033[93m'
COLOR_MAGENTA = '\033[95m'
COLOR_RESET = '\033[0m'

# --- Configuración del puerto serie ---
PUERTO_SERIE = 'COM5'
BAUD_RATE = 1843200




# ----------------------------
# Simulated Serial Interface
# ----------------------------
class DZETester:
    def __init__(self, callback):
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
        self.CorrienteFLux = 0.0
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

            # self.hilo_enviar.join()
            # self.hilo_recibir.join()

        except serial.SerialException as e:
            print(f"Error abriendo puerto serie: {e}")
            self.ser = None


    def stop(self):
        self.running = False

    def send(self, cmd, description=""):
        try:
            self.ser.flush()
            self.ser.write( bytes.fromhex(cmd[0:8]))
            time.sleep(0.002)
            self.ser.write( bytes.fromhex(cmd[8:]))
            print(f"{COLOR_AZUL}TX: {description} : ({cmd}){COLOR_RESET}")
        except serial.SerialException as e:
            print(f"Error al enviar datos: {e}")
        time.sleep(0.1)

    def configurar_placa(self):
        i=0
        
        mensajes = ["85FFFFBF",
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
                    "D900004008002905070000040000FF0000"]
        
        with self.condition:

            while i < len(mensajes):
                
                try:
                    self.ser.flush()
                    self.ser.write( bytes.fromhex(mensajes[i][0:8]))
                    time.sleep(0.002)
                    self.ser.write( bytes.fromhex(mensajes[i][8:]))

                    print(f"{COLOR_AZUL}Enviado: {mensajes[i]}{COLOR_RESET}")
                except serial.SerialException as e:
                    print(f"Error al enviar datos: {e}")
                    break
                time.sleep(0.1)
                i += 1
            print(f"{COLOR_AZUL}Enviado: PLACA CONECTADA {COLOR_RESET}")
            self.msg_gui = "Placa configurada y conectada."
            self.condition.notify_all()      #comienzo a enviar datos

    def keep_alive_status(self):
        time.sleep(2)  # Espera inicial antes de comenzar el keep-alive
        mensaje = "A9040070110019005900591B9900D90019019102D10251099101D101911451149100D1009109D1081109D105910551039103910451041119D118910B510BD10B110C510C910CD11A49008900C900"
        with self.condition:
            #self.condition.wait()  # Espera hasta que la placa esté configurada - se traba, resuelto con sleep
            while True:
                self.send(mensaje, "Lectura status")
                time.sleep(0.2)

    def SetearCorrienteCarga(self, corriente):              
        self.CorrienteCarga = corriente/1000.0  # Convertir mA a A
        mensaje_base = "6900000008009100"  
        porcentaje_hex = struct.pack('<h', corriente).hex()
        msj = mensaje_base + porcentaje_hex
        print(f"{COLOR_MAGENTA}Seteando Corriente de Carga a {corriente} mA ({msj})")
        self.send(msj, f"Seteo Corriente de Carga a {corriente} mA")


    def SetearCorrientePruebaRegParalelo(self, corriente):              #0x69000000080091095302 
        self.CorrienteEnsayo = corriente/1000.0  # Convertir mA a A
        corriente = int(corriente/0.0006715014773/1000)
        mensaje_base = "6900000008009109"  
        porcentaje_hex = struct.pack('<h', corriente).hex()
        msj = mensaje_base + porcentaje_hex
        self.send(msj, f"Seteo Corriente de ensayo a {corriente}")



    def recibir_datos(self):
        cmd = ""
        while True:
            try:
                if self.ser.in_waiting > 0:
                    datos_recibidos = self.ser.read(self.ser.in_waiting)
                    # Convierte los bytes recibidos a una cadena hexadecimal
                    hex_representation = datos_recibidos.hex()
                    if(hex_representation == "1a00002000"):
                        print(f"{COLOR_ROJO}RX: Comando recibido OK! - ({hex_representation})")

                    if(hex_representation.startswith("2a050040")):  
                        byte_data = bytes.fromhex(hex_representation[88:92])
                        tension_mV = struct.unpack('<h', byte_data)[0]
                        self.TensionSalida = tension_mV / 1000.0  # Convertir mV a V
                        print(f"{COLOR_ROJO}RX: TENSION {self.TensionSalida} - ({hex_representation})")

                    if(hex_representation.startswith("e93f00b0")):
                        hex_str = hex_representation[16::]  
                        if len(hex_str) % 4 != 0:
                            raise ValueError("Hex string length must be a multiple of 4 for int16 values.")

                        chunks = [hex_str[i:i+4] for i in range(0, len(hex_str), 4)]
                        int16_array = []
                        for chunk in chunks:
                            # Convert hex string to bytes
                            byte_data = bytes.fromhex(chunk)
                            # Unpack as big-endian signed 16-bit integer
                            value = struct.unpack('<h', byte_data)[0]
                            int16_array.append(value)

                        rms = np.sqrt(np.mean(np.square(int16_array)))
                        print("RMS:", rms)


            except serial.SerialException as e:
                print(f"Error al recibir datos: {e}")
                break
            time.sleep(0.1)

    def ProbarReguladorSerie(self):
        #Paso a modo regulador serie
        print(f"{COLOR_VERDE}--- PROBANDO REGULADOR SERIE ---")
        self.msg_gui = "Iniciando prueba regulador serie..."

        # Comando configuracion serie: 0x590000F00800890001
        self.send("590000F00800890002", "Configurar modo regulador serie")

        mensaje_base = "690000000800D11A"   #690000000800D11Axxxx - Porcentaje 0 - 100
        for porcentaje in range(0, 101, 5):
            porcentaje_hex = struct.pack('<h', porcentaje).hex()
            mensaje = mensaje_base + porcentaje_hex
            time.sleep(0.1)

    def ProbarReguladorParalelo(self):
        print(f"{COLOR_VERDE}--- PROBANDO REGULADOR PARALELO ---")
        self.msg_gui = "Iniciando prueba regulador paralelo..."


        self.send("290000E03900", "ACK Error previo")

        #Envio comandos para probar regulador paralelo - 
        self.send("590000F00800890002", "Configurar modo regulador paralelo")


        # Seteo corriente de carga de 0 a 400mA
        for mA in range(0, 401, 50):
            self.SetearCorrienteCarga(mA)  # Ejemplo: 0 a 400 mA
            time.sleep(0.05)

        # Start inversor
        self.send("290000E01900", "Comando Start")

        # Seteo corriente de prueba del regulador paralelo de 0 a 500mA
        for mA in range(0, 1201, 100):
            self.SetearCorrientePruebaRegParalelo(mA)  # Ejemplo: 0 a 500 mA
            time.sleep(0.05)
    
        self.send("F9000030080029050900FE030001FF00D10711","Datos Ia")


        time.sleep(10)
        self.send("290000E02100", "Comando Stop")



# ----------------------------
# Root Widget
# ----------------------------
class ControlPanel(BoxLayout):
    mode_text = StringProperty("Idle")
    indicators = DictProperty({
        "Overvoltage": False,
        "Overtemperature": False,
        "Error": False,
        "Overcurrent Protection": False,
        "Running": False,
        "Connected": False
    })

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.DZE = DZETester(self.log_serial)
        Clock.schedule_interval(self.update_values, 0.1)

    def update_values(self, dt):
        self.ids.tension_salida.text = f"{self.DZE.TensionSalida} V"

    def log_serial(self, message, incoming=True):
        self.ids.console.text += message + '\n'
        self.ids.console.cursor = (0, len(self.ids.console.text))

        if "FAULT:" in message:
            fault = message.split("FAULT:")[-1].strip()
            if fault == "OVERVOLTAGE":
                self.indicators["Overvoltage"] = True
            elif fault == "OVERTEMP":
                self.indicators["Overtemperature"] = True
            elif fault == "OVERCURRENT":
                self.indicators["Overcurrent Protection"] = True
            elif fault == "ERROR":
                self.indicators["Error"] = True

    def set_indicator(self, name, active):
        self.indicators[name] = active

    def on_rpm_change(self, value):
        self.DZE.send(f"RPM {int(value)}", f"Set RPM to {int(value)}")

    def on_current_change(self, value):
        self.DZE.send(f"CURR {value:.1f}", f"Set current to {value:.1f} A")

    def on_voltage_change(self, value):
        self.DZE.send(f"VOLT {value:.1f}", f"Set voltage to {value:.1f} V")

    def connect(self):
        print("Inicializando interfaz serial...")
        self.DZE.start()
        self.indicators["Connected"] = True
        self.ids.btn_conectar.text = "Connected"
        self.ids.btn_conectar.disabled = True


    def reset_error(self):
        self.DZE.send("RESET ERR", "Reset error state")
        for key in self.indicators:
            self.indicators[key] = False
        self.mode_text = "Idle"

    def on_stop(self):
        self.DZE.stop()

    # Command handlers
    def run_serie_test(self):
        # ak.start(self.TaskProbarReguladorSerie())
        threading.Thread(target=self.DZE.ProbarReguladorSerie).start()
        self.mode_text = "Probando regulador"

    # async def TaskProbarReguladorSerie(self):
    #     await asyncio.to_thread(self.DZE.ProbarReguladorSerie())
        
        
    #     print(f"{COLOR_VERDE}--- FIN PRUEBA REGULADOR SERIE ---")


    def run_shunt_test(self):
        threading.Thread(target=self.DZE.ProbarReguladorParalelo).start()
        # ak.start(self.TaskProbarReguladorParalelo())
        self.mode_text = "Probando regulador"

    async def TaskProbarReguladorParalelo(self):
        await asyncio.to_thread(self.DZE.ProbarReguladorParalelo())
        print(f"{COLOR_VERDE}--- FIN PRUEBA REGULADOR PARALELO ---")




# ----------------------------
# Main App
# ----------------------------
class ControlApp(App):
    def build(self):
        return ControlPanel()

    def on_stop(self):
        self.root.on_stop()


# ----------------------------
if __name__ == '__main__':
    ControlApp().run()
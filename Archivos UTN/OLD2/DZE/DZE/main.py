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

import matplotlib.pyplot as plt

from collections import deque

import numpy as np

COLOR_AZUL = '\033[94m'
COLOR_ROJO = '\033[91m'
COLOR_VERDE = '\033[32m'
COLOR_MAGENTA = '\033[95m'
COLOR_RESET = '\033[0m'
COLOR_AMARILLO = '\033[33m'

# --- Configuración del puerto serie ---
PUERTO_SERIE = 'COM5'
BAUD_RATE = 1843200




# ----------------------------
# Simulated Serial Interface
# ----------------------------
class DZETester:
    def __init__(self):
        self.running = False
        self.condition = threading.Condition()

        self.hilo_enviar = threading.Thread(target=self.keep_alive_status)
        self.hilo_recibir = threading.Thread(target=self.recibir_datos)

        self.hilo_enviar.daemon = True
        self.hilo_recibir.daemon = True

        self.TensionSalida = 0.0
        self.TensionSalidaMedia = 0.0
        self.CorrienteCarga = 0.0
        self.CorrienteEnsayo = 0.0
        self.RPM = 800
        self.msg_gui = ""

        self.IaRMS = 0.0
        self.IbRMS = 0.0
        self.IcRMS = 0.0
        self.IaAVG = 0.0
        self.IbAVG = 0.0
        self.IcAVG = 0.0

        self.DispositivoEstado = ["Dispositivo OK","Dispositivo no conduce/abierto","Dispositivo en cortocircuito","Fase abierta"]
        self.EstadoEnsayo = 0  # 0: Espera, 1: Ejecutando, 2: Ensayo OK, 3: Ensayo ERRROR
        self.DispositivoFaseA = 0 #0: Dispositivo OK, 1: Dispositivo Abierto, 2: Dispositivo en cortocircuito, 3: Fase abierta
        self.DispositivoFaseB = 0
        self.DispositivoFaseC = 0

        # Create a fixed-length deque of size 50 to store the data points
        self.data_points = deque(maxlen=50)
        self.fig, self.ax = plt.subplots()
        self.line = self.ax.plot([])


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
            if not(description.startswith("NP:")):      #si la descripcion empieza con NP no la imprimo
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
                self.send(mensaje, "NP:Lectura status")
                time.sleep(0.2)

    def SetearCorrienteCarga(self, corriente):              
        self.CorrienteCarga = corriente/1000.0  # Convertir mA a A
        mensaje_base = "6900000008009100"  
        porcentaje_hex = struct.pack('<h', corriente).hex()
        msj = mensaje_base + porcentaje_hex
        #print(f"{COLOR_MAGENTA}Seteando Corriente de Carga a {corriente} mA ({msj})")
        self.send(msj, f"NP:Seteo Corriente de Carga a {corriente} mA")


    def SetearCorrientePruebaRegParalelo(self, corriente):              #0x69000000080091095302 
        self.CorrienteEnsayo = corriente/1000.0  # Convertir mA a A
        corriente = int(corriente/0.0006715014773/1000)
        mensaje_base = "6900000008009109"  
        porcentaje_hex = struct.pack('<h', corriente).hex()
        msj = mensaje_base + porcentaje_hex
        self.send(msj, f"NP:Seteo Corriente de ensayo a {corriente}")

    def hex_to_int16_array(self,hex_str):
        import struct
        hex_str_data = hex_str[16::]         
            # 0x2FCF3F01  (20959023)
            #0xE93F00B0 0x4C1BBE00  (12458828)
        if len(hex_str_data) % 4 == 0:
            chunks = [hex_str_data[i:i+4] for i in range(0, len(hex_str_data), 4)]
            int16_array = np.array([], dtype=np.int16)
            for chunk in chunks:
                byte_data = bytes.fromhex(chunk)
                value = struct.unpack('<h', byte_data)[0]
                int16_array = np.append(int16_array, value)

            ia_array =  np.array([], dtype=np.int16)
            ib_array =  np.array([], dtype=np.int16)  
            ic_array =  np.array([], dtype=np.int16)
            for i in range(len(int16_array)//2):
                ia_array = np.append(ia_array, int16_array[i*2])
                ib_array = np.append(ib_array, int16_array[i*2+1])
            # ia+ib+ic=0 -> ic = - (ia + ib)
            ic_array = - (ia_array + ib_array)

            return [ia_array, ib_array, ic_array]
        return [0,0,0]

    def recibir_datos(self):
        cmd = ""
        while True:
            try:
                if self.ser.in_waiting > 0:
                    datos_recibidos = self.ser.read(self.ser.in_waiting)

                    # Convierte los bytes recibidos a una cadena hexadecimal
                    hex_representation = datos_recibidos.hex()
                    
                    #if(hex_representation == "1a00002000"):            #Comando recibido OK
                    #   print(f"{COLOR_ROJO}RX: Comando recibido OK! - ({hex_representation})")

                    if(hex_representation.startswith("2a050040")):  
                        byte_data = bytes.fromhex(hex_representation[88:92])
                        if(len(byte_data) >= 2):
                            tension_mV = struct.unpack('<h', byte_data)[0]
                            self.TensionSalida = tension_mV / 1000.0  # Convertir mV a V
                            self.TensionSalidaMedia = self.TensionSalidaMedia + ( self.TensionSalida - self.TensionSalidaMedia ) * 0.1      #filtro FIR 1er orden
                            #print(f"{COLOR_ROJO}RX: TENSION {self.TensionSalida} ")

                    # print("DATOS BRUTOS:", hex_representation)
                    #A93F0050F27142015E032000FE0290FF8E02C0FF8E0290FF5E02B0FFEE01F0FF5E02B0FF1E02E0FF10016E00B0005E0040005E00D0FF3E00D0013E002004BEFF20051E00A0FA7E05F0043E0002052E00A2032E0012025E004200BEFFA2FE2E0032FD4E0082FB3E00F2F94E00C2F72E0042F93E00C2FAA0FF82FBA0FF32FC90FFB2FC90FF22FD70FF02FDB0FF32FDE0FF62FDE0FFF001D2FD500172FE30FFC2FF80FF0200C0FF1200E0FD0200A0FC0200F0FBF2FFDEFC02007EFDE2FF5EFEF2FFBEFFE2FFEE003200EE01F2FF9E0202000E05D2FFCE06E2FFCE05F2FF2E00B2FB7E0300006E03C0FF2E034000DE02B0FFDE02A0FFCE0280FF7E02E0FF8E0280FF70015E003001DEFF20005E00A0FF5E00E0FF3E0080013E00D0022E0060033E0080FC7E0320FD0E0352022E0062011E00C2FF4E0042FE3E00E2FC1E0042FB4E0042F91E0022F83E0092F92E00C2FAC0FFA2FBA0FF72FC80FFB2FCC0FFF2FC90FF02FDF0FF52FDC0FFD2FCD000800132FE1001C2FE30FFF2FFE0FFF2FF20FEF2FF80FCF2FF20FB120010FBF2FF3EFC1200FEFC22001EFE12009EFF2200CE00F2FFCE02E2FF6E0302002E05F2FFCE06D2FFDE05E2FFFEFFB2FB7E03E0FF5E03D0FF3E0390FFEE02D0FFCE02C0FFBE02A0FF6E02E0FF4E0280FF40014E00E0003E0040003E00C0FF4E00C0014E0060032E0030043E0000FBFE04D004BEFF32043E00C2022E0032012E00B2FF3E0012FE3E0072FC1E00E2FABEFFF2F81E00D2F84E00C2F93E0012FB70FFC2FBD0FF42FCC0FFA2FC30FFE2FCA0FF02FDD0FF42FDD0FF92FDB00040FEF2FFD0FEF2FFF0FEE2FFF0FFF2FF20FE1200B0FCF2FFB0FBF2FF50FB12007EFCF2FF4EFDF2FF6EFE1200EEFFF2FF3E0102006E024200EE03F2FFAE05C2FF6E06D2FF3E05E2FFDE0320003E03C0FF7E0240009E0290FF8E02B0FF5E02E0FF6E02A0FF4E02C0FF0E02B0FFD0FF5E0080003E00E0FF7E00D0FF4E00A0014E0020033E0010043E00B0FB8E0430042E00A2033E0062022E00B2001E0022FF1E00B2FD2E00D2FC1E00D2FA0E00D2F83E00C2F83E0012FA3E0032FBC0FFF2FB90FF92FC90FFC2FCC0FFF2FCE0FF32FDC0FF72FDC0FFB2FD200080FEE2FF00FFF2FFA0FF02000000F2FF30FE0200C0FCF2FFE0FBF2FFB0FB0200CEFCF2FFAEFD0200EEFE32005E00E2FF8E01E2FFCE0202004E04F2FF6E0502008E06D2FFFE04D2FF8E033000AE0350FFAE02E0FF6E02D0FF7E02D0FF8E02B0FF5E02B0FF6E0280FFE001DEFFF0004E0080003E00E0FF3E00C0FF3E00C0013E00E0023E00A0031E00D0FB5E04A0034E0042033E00E2013E0042004E00D2FE3E0072FD3E00F2FB6E0002FA4E0042F82E00C2F83E0082FA90FF72FB90FF82FC20FF72FCC0FFC2FCB0FF02FDB0FF02FDD0FF62FDC0FF0002D2FD0002D2FDC0FEE2FF0300
                    if(hex_representation.startswith("a93f0050")):
                        
                        [ia_array, ib_array, ic_array] = self.hex_to_int16_array(hex_representation)

                        if type(ia_array) == int:
                            continue

                        self.IaRMS = np.sqrt(np.mean(np.square(ia_array)))
                        self.IbRMS = np.sqrt(np.mean(np.square(ib_array)))
                        self.IcRMS = np.sqrt(np.mean(np.square(ic_array)))

                        # print(f"RMS: IaRMS {self.IaRMS:5.1f} - IbRMS {self.IbRMS:5.1f} - IcRMS {self.IcRMS:5.1f}")
                        # print("DATOS BRUTOS:", hex_representation)

                        self.IaAVG = np.mean(ia_array)
                        self.IbAVG = np.mean(ib_array)
                        self.IcAVG = np.mean(ic_array)
                        #print("Average: Iavg", self.IaAVG," - Iavg" ,self.IbAVG," - Iavg", self.IcAVG)

            except serial.SerialException as e:
                print(f"Error al recibir datos: {e}")
                break
            time.sleep(0.01)

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
        self.EstadoEnsayo = 1  # Ejecutando

        self.DispositivoFaseA = 0
        self.DispositivoFaseB = 0
        self.DispositivoFaseC = 0

        self.send("290000E03900", "ACK Error previo")
        self.send("590000F00800890002", "Configurar modo regulador paralelo")

        # Seteo corriente de carga
        for mA in range(0, 201, 50):
            self.SetearCorrienteCarga(mA)  
            time.sleep(0.05)
        # Start inversor y pido muestas Ia e Ib
        self.send("F9000030080029050900FE030001FF00D10713","Datos Ia")  #07D1 in decimal is 2001  F9000030080029050900FE030001FF00D10713
        self.send("190100A0080029050B00FC030002FF00D107110814","Datos Ib")  #0811 in decimal is 2065  0x190100A0080029050B00FC030002FF00D10711080F
        time.sleep(0.1)
        self.send("290000E01900", "Comando Start")

        # Seteo corriente de prueba del regulador paralelo de 0 a xxmA
        for mA in range(0, 400, 100):
            self.SetearCorrientePruebaRegParalelo(mA) 
            time.sleep(0.1)
        time.sleep(0.5)


        # 1) Ensayo falta de fase 
        print(f"{COLOR_AMARILLO} 1)Ensayo falta de fase {COLOR_RESET}" )
        IaRMS_cola = []
        IbRMS_cola = []
        IcRMS_cola = []

        IaAVG_cola = [] 
        IbAVG_cola = []
        IcAVG_cola = []

        for dt in range(10):
            IaAVG_cola.append(self.IaAVG)
            IaRMS_cola.append(self.IaRMS)  
            IbAVG_cola.append(self.IbAVG)
            IbRMS_cola.append(self.IbRMS)  
            IcAVG_cola.append(self.IcAVG)
            IcRMS_cola.append(self.IcRMS)  
            time.sleep(0.1)

        ValorMedioGeneral_A =  np.mean(IaAVG_cola)
        ValorRMSGeneral_A =  np.mean(IaRMS_cola)
        ValorMedioGeneral_B =  np.mean(IbAVG_cola)
        ValorRMSGeneral_B =  np.mean(IbRMS_cola)
        ValorMedioGeneral_C =  np.mean(IcAVG_cola)
        ValorRMSGeneral_C =  np.mean(IcRMS_cola)


        print("Muestras:", len(IaRMS_cola))
        print(f"RMS: IaRMS {ValorRMSGeneral_A:5.1f} - IbRMS {ValorRMSGeneral_B:5.1f} - IcRMS {ValorRMSGeneral_C:5.1f}")
        print(f"AVG: IaAVG {ValorMedioGeneral_A:5.1f} - IbAVG {ValorMedioGeneral_B:5.1f} - IcAVG {ValorMedioGeneral_C:5.1f}")


        maxRMS = max([ValorRMSGeneral_A,ValorRMSGeneral_B,ValorRMSGeneral_C])
        desvio_RMS_entre_fases_maximo = 0.2*maxRMS
        print(f"maxRMS:{maxRMS:5.1f} - DesvioRMSmax :{desvio_RMS_entre_fases_maximo:5.1f}")

        if(abs(ValorRMSGeneral_A-maxRMS) > desvio_RMS_entre_fases_maximo):
            self.DispositivoFaseA = 3  # Fase Abierta
        if(ValorMedioGeneral_A < -500):
            self.DispositivoFaseA = 1  # Dispositivo Abierto

        if(abs(ValorRMSGeneral_B-maxRMS) > desvio_RMS_entre_fases_maximo):
            self.DispositivoFaseB = 3  # Fase Abierta
        if(ValorMedioGeneral_B < -500):
            self.DispositivoFaseB = 1  # Dispositivo Abierto

        if(abs(ValorRMSGeneral_C-maxRMS) > desvio_RMS_entre_fases_maximo):
            self.DispositivoFaseC = 3  # Fase Abierta
        if(ValorMedioGeneral_C < -500):
            self.DispositivoFaseC = 1  # Dispositivo Abierto

        print(f"{COLOR_AMARILLO}Ensayo falta de fase: A: {self.DispositivoEstado[self.DispositivoFaseA]} - B: {self.DispositivoEstado[self.DispositivoFaseB]} - C: {self.DispositivoEstado[self.DispositivoFaseC]}")

        # 2) Ensayo dispositivo en no dispara
        # Seteo corriente de prueba del regulador paralelo de 0 a xxmA
        print(f"{COLOR_AMARILLO} 2) Ensayo funcionamiento dispositivos {COLOR_RESET}" )
        
        for mA in range(400, 1001, 100):
            self.SetearCorrientePruebaRegParalelo(mA) 
            time.sleep(0.1)
         
        for mA in range(400, 2500, 100):
            self.SetearCorrientePruebaRegParalelo(mA) 
            time.sleep(0.1)
        time.sleep(1.5)

        for mA in range(2500, 1100, 100):
            self.SetearCorrientePruebaRegParalelo(mA) 
            time.sleep(0.1)
        time.sleep(0.3)


        IaRMS_cola.clear()
        IbRMS_cola.clear()
        IcRMS_cola.clear()

        IaAVG_cola.clear() 
        IbAVG_cola.clear()
        IcAVG_cola.clear()

        for dt in range(10):
            IaAVG_cola.append(self.IaAVG)
            IaRMS_cola.append(self.IaRMS)  
            IbAVG_cola.append(self.IbAVG)
            IbRMS_cola.append(self.IbRMS)  
            IcAVG_cola.append(self.IcAVG)
            IcRMS_cola.append(self.IcRMS)  
            time.sleep(0.1)

        ValorMedioGeneral_A =  np.mean(IaAVG_cola)
        ValorRMSGeneral_A =  np.mean(IaRMS_cola)
        ValorMedioGeneral_B =  np.mean(IbAVG_cola)
        ValorRMSGeneral_B =  np.mean(IbRMS_cola)
        ValorMedioGeneral_C =  np.mean(IcAVG_cola)
        ValorRMSGeneral_C =  np.mean(IcRMS_cola)

        # print("IaAVG",IaAVG_cola)
        # print("IbAVG",IbAVG_cola)
        # print("IcAVG",IcAVG_cola)

        print("Muestras:", len(IaRMS_cola))
        print(f"RMS: IaRMS {ValorRMSGeneral_A:5.1f} - IbRMS {ValorRMSGeneral_B:5.1f} - IcRMS {ValorRMSGeneral_C:5.1f}")
        print(f"AVG: IaAVG {ValorMedioGeneral_A:5.1f} - IbAVG {ValorMedioGeneral_B:5.1f} - IcAVG {ValorMedioGeneral_C:5.1f}")

        maxRMS = max([ValorRMSGeneral_A,ValorRMSGeneral_B,ValorRMSGeneral_C])
        comparacionRMS = 0.2*maxRMS
        print(f"maxRMS:{maxRMS:5.1f} - DesvioRMSmax :{desvio_RMS_entre_fases_maximo:5.1f}")

        if(ValorMedioGeneral_A < -500):
            self.DispositivoFaseA = 1  # Dispositivo Abierto

        if(ValorMedioGeneral_B < -500):
            self.DispositivoFaseB = 1  # Dispositivo Abierto

        if(ValorMedioGeneral_C < -500):
            self.DispositivoFaseC = 1  # Dispositivo Abierto
        
        print(f"{COLOR_AMARILLO}Ensayo conducción MOS: A: {self.DispositivoEstado[self.DispositivoFaseA]} - B: {self.DispositivoEstado[self.DispositivoFaseB]} - C: {self.DispositivoEstado[self.DispositivoFaseC]}")


        print(f"{COLOR_AMARILLO} 3) Ensayo regulacion de tensión {COLOR_RESET}" )

        for mA in range(1000, 100, 100):
            self.SetearCorrientePruebaRegParalelo(mA) 
            time.sleep(0.1)
         
        for mA in range(1000, 2000, 100):
            self.SetearCorrientePruebaRegParalelo(mA) 
            time.sleep(0.1)
        time.sleep(1.5)


        Vout_cola = []
        for dt in range(10):
            Vout_cola.append(self.TensionSalida)
            time.sleep(0.1)

        Vout_medio =  np.mean(Vout_cola)

        if (abs(Vout_medio - 14.6) > 0.2):      
            print(f"{COLOR_ROJO}--- ERROR EN ENSAYO REGULADOR PARALELO - Tensión: {Vout_medio} V ---")
            self.msg_gui = "Error en ensayo regulador paralelo. Tensión fuera de rango."
            self.EstadoEnsayo = 3  # Ensayo ERROR
        else:
            print(f"{COLOR_VERDE}--- ENSAYO REGULADOR PARALELO OK - Tensión: {Vout_medio} V ---")
            self.msg_gui = "Ensayo regulador paralelo OK. Tensión dentro de rango."
            self.EstadoEnsayo = 2  # Ensayo OK
        time.sleep(0.2)

        self.send("290000E02100", "Comando Stop")
        self.EstadoEnsayo = 2  # Ensayo OK  



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
        self.DZE = DZETester()
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
        threading.Thread(target=self.DZE.ProbarReguladorSerie).start()
        self.mode_text = "Probando regulador" 

    def run_shunt_test(self):
        threading.Thread(target=self.DZE.ProbarReguladorParalelo).start()
        self.mode_text = "Probando regulador"




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
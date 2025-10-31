import os
import time
import threading
from flask import Flask
from concurrent.futures import ThreadPoolExecutor
from flask_cors import CORS
import webbrowser
import subprocess
import sys

from engine.ProbadorHandler.mainOLD import DZETester
from engine.serialUtils.SerialFinder import find_stlink
from engine.routes.routes import register_routes

# ------------------------
# Configuración
# ------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIST_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "Frontend", "dist"))

BAUDRATE = 1843200  # Velocidad del DZE Tester
log_buffer = []

# ------------------------
# Callback de eventos serie
# ------------------------
def serial_callback(message):
    log_buffer.append(message)
    print(message)

# ------------------------
# Inicializar DZE Tester
# ------------------------
dze_tester = DZETester()

def inicializar_serial():
    print("Inicializando interfaz serial...")
    while True:
        found, PuertoSerie = find_stlink()
        if found:
            print(f"Placa encontrada en: {PuertoSerie}")
            dze_tester.start(PuertoSerie)
            break
        else:
            print("No se encontró la placa STLink, reintentando en 1 segundo...")
            time.sleep(1)

def on_stop():
    if dze_tester:
        dze_tester.stop()

# ------------------------
# Ejecución de ensayo
# ------------------------
def run_shunt_test():
    with ThreadPoolExecutor(max_workers=1) as executor:
        futuro = executor.submit(dze_tester.ProbarReguladorParalelo)
        resultado = futuro.result()
    return resultado

# ------------------------
# Configurar Flask
# ------------------------
app = Flask(__name__, static_folder=FRONTEND_DIST_PATH, static_url_path="")
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})
register_routes(app, FRONTEND_DIST_PATH, dze_tester, log_buffer, inicializar_serial)

# ------------------------
# Servidor Flask
# ------------------------
def start_flask():
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)

# ------------------------
# Abrir navegador en fullscreen
# ------------------------
def abrir_navegador_fullscreen(url="http://localhost:5000"):
    try:
        if sys.platform.startswith("win"):
            chrome_path = "C:/Program Files/Google/Chrome/Application/chrome.exe"
            if not os.path.exists(chrome_path):
                chrome_path = "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"
            if os.path.exists(chrome_path):
                os.system(f'start "" "{chrome_path}" --start-fullscreen "{url}"')
            else:
                print("Chrome no encontrado, abriendo navegador por defecto...")
                webbrowser.open(url)
        elif sys.platform.startswith("darwin"):
            subprocess.Popen([
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "--start-fullscreen",
                url
            ])
        else:
            subprocess.Popen(["google-chrome", "--start-fullscreen", url])
    except Exception as e:
        print("No se pudo abrir el navegador en fullscreen:", e)
        webbrowser.open(url)

if __name__ == "__main__":
    # Iniciar hilo Flask
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()
    print("Servidor Flask iniciado.")

    # Abrir navegador en pantalla completa
    abrir_navegador_fullscreen("http://localhost:5000")

    # Inicializar comunicación serie
    inicializar_serial()

    print("Comunicación con DZETester activa.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Cerrando servidor Flask y comunicación serie...")
        on_stop()

import os
import sys
import signal
import subprocess
from flask import jsonify, send_from_directory
from concurrent.futures import ThreadPoolExecutor
import threading
from engine.ProbadorHandler.restartSerial import reiniciar_serial

def register_routes(app, frontend_dist_path, dze_tester, log_buffer, inicializar_serial):
    
    @app.route('/testregulator', methods=['POST'])
    def test_regulator():
        if not dze_tester:
            return jsonify({"status": "error", "message": "DZETester no inicializado"})
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                futuro = executor.submit(dze_tester.ProbarReguladorParalelo)
                resultado = futuro.result()
            return jsonify({"status": "ok", "resultado": resultado})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    
    @app.route("/reiniciar-serial", methods=["POST"])
    def route_reiniciar_serial():
        resultado = reiniciar_serial(dze_tester, inicializar_serial)
        return jsonify(resultado)

    # ------------------------
    # Servir frontend
    # ------------------------
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path):
        if path != "" and os.path.exists(os.path.join(frontend_dist_path, path)):
            return send_from_directory(frontend_dist_path, path)
        else:
            return send_from_directory(frontend_dist_path, "index.html")

    # ------------------------
    # Ruta de apagado
    # ------------------------
    @app.route("/shutdown-system", methods=["POST"])
    def shutdown_system():
        try:
            # Detener DZETester
            if dze_tester:
                dze_tester.stop()

            # Cerrar navegador Chrome (Windows)
            if sys.platform.startswith("win"):
                subprocess.call('taskkill /F /IM chrome.exe', shell=True)
            elif sys.platform.startswith("darwin"):
                subprocess.call(["pkill", "-f", "Google Chrome"])
            else:
                subprocess.call(["pkill", "-f", "chrome"])

            # Cerrar Flask y salir del programa
            threading.Thread(target=lambda: os._exit(0), daemon=True).start()

            return jsonify({"status": "ok", "message": "Sistema apagado"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})

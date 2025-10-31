import time

def reiniciar_serial(dze_tester, inicializar_serial):
    """Reinicia la comunicación serie con la placa."""
    print("Reiniciando comunicación serie...")
    if dze_tester:
        try:
            dze_tester.stop()
        except Exception as e:
            print("Error cerrando puerto:", e)
        time.sleep(2)
    inicializar_serial()
    return {"status": "ok", "message": "Comunicación serie reiniciada"}

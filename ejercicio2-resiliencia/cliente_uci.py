# cliente_uci.py
# Simula el monitor cardiaco de la UCI consultando la IA en la nube
# a través del Circuit Breaker. Imprime el estado en cada llamada.

import time
import urllib.request
from circuit_breaker import CircuitBreaker

URL_IA = "http://127.0.0.1:8000/analizar"
TIMEOUT = 0.8                       # Timeout por llamada = 800 ms (tabla de la guía)

cb = CircuitBreaker()               # Usa los parámetros por defecto de la guía


def llamar_ia_nube(muestra):
    # Llamada HTTP real a la "nube"; lanza excepción si hay timeout o error
    with urllib.request.urlopen(URL_IA, timeout=TIMEOUT) as r:
        return r.read().decode()


def fallback_local(muestra):
    # Análisis básico local (caché / modelo ligero en el Edge de la UCI)
    return "analisis local: ritmo estable"


print("Cliente UCI iniciado. Ctrl+C para salir.\n")
n = 0
while True:
    n += 1
    resultado, origen = cb.llamar(llamar_ia_nube, fallback_local, n)
    print(f"[{n:03d}] estado={cb.estado.value:<9} | origen={origen}")
    time.sleep(0.25)                # 4 muestras por segundo



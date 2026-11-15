# ia_nube_simulada.py
# Simula el servicio de IA de arritmias en la nube pública.
# Permite configurar una latencia artificial para probar el Circuit Breaker.

import argparse                      # Para leer argumentos de la terminal
import json                          # Para responder en formato JSON
import time                          # Para simular la latencia (sleep)
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Leemos el argumento --latencia (segundos que tardará en responder)
parser = argparse.ArgumentParser()
parser.add_argument("--latencia", type=float, default=0.0,
                    help="Segundos que tarda cada respuesta (ej: 0.6 o 0.9)")
args = parser.parse_args()


class Manejador(BaseHTTPRequestHandler):
    def do_GET(self):
        time.sleep(args.latencia)    # Simula una nube lenta
        cuerpo = json.dumps({"analisis": "ritmo normal"}).encode()
        self.send_response(200)      # Respondemos OK
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(cuerpo)

    def log_message(self, formato, *a):
        pass                         # Silenciamos el log por defecto


print(f"IA nube simulada en http://127.0.0.1:8000 | latencia = {args.latencia}s")
# ThreadingHTTPServer atiende varias peticiones a la vez
ThreadingHTTPServer(("127.0.0.1", 8000), Manejador).serve_forever()


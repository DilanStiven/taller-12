# circuit_breaker.py
# Circuit Breaker hecho a mano con los parámetros de la guía (Paso 2.1).

import threading                     # Lock para proteger el estado compartido
import time                          # Medir duración de llamadas
from collections import deque        # Ventana deslizante de tamaño fijo
from enum import Enum


class Estado(Enum):
    CLOSED = "CLOSED"                # Las llamadas pasan y se miden
    OPEN = "OPEN"                    # Se rechazan de inmediato (fail-fast)
    HALF_OPEN = "HALF_OPEN"          # Se permiten pocas llamadas de prueba


class CircuitBreaker:
    def __init__(self,
                 ventana=20,              # Sliding window COUNT_BASED = 20 llamadas
                 minimo_llamadas=10,      # No evaluar con menos de 10 llamadas
                 umbral_fallos=0.20,      # Failure Rate Threshold = 20 %
                 umbral_lentas=0.30,      # Slow Call Rate Threshold = 30 %
                 duracion_lenta=0.5,      # Slow Call Duration = 500 ms
                 espera_open=15.0,        # Wait Duration in Open State = 15 s
                 pruebas_half_open=3):    # Permitted Calls in Half-Open = 3
        self.ventana = deque(maxlen=ventana)   # Guarda tuplas (ok, lenta)
        self.minimo_llamadas = minimo_llamadas
        self.umbral_fallos = umbral_fallos
        self.umbral_lentas = umbral_lentas
        self.duracion_lenta = duracion_lenta
        self.espera_open = espera_open
        self.pruebas_half_open = pruebas_half_open
        self.estado = Estado.CLOSED
        self.t_apertura = 0.0
        self.pruebas_lanzadas = 0              # Pruebas enviadas en HALF_OPEN
        self.pruebas_ok = 0                    # Pruebas exitosas en HALF_OPEN
        self.lock = threading.Lock()

    # ---- Cambios de estado ------------------------------------------------
    def _abrir(self):
        self.estado = Estado.OPEN
        self.t_apertura = time.monotonic()     # Guardamos cuándo se abrió

    def _cerrar(self):
        self.estado = Estado.CLOSED
        self.ventana.clear()                   # Empezamos con historial limpio

    # ---- Tasas sobre la ventana ------------------------------------------
    def tasa_fallos(self):
        return sum(1 for ok, _ in self.ventana if not ok) / len(self.ventana)

    def tasa_lentas(self):
        return sum(1 for _, lenta in self.ventana if lenta) / len(self.ventana)

    # ---- Método principal -------------------------------------------------
    def llamar(self, funcion, fallback, *argumentos):
        """Devuelve (resultado, origen). origen indica de dónde vino la respuesta."""
        with self.lock:
            if self.estado == Estado.OPEN:
                if time.monotonic() - self.t_apertura >= self.espera_open:
                    self.estado = Estado.HALF_OPEN     # Ya pasaron los 15 s
                    self.pruebas_lanzadas = 0
                    self.pruebas_ok = 0
                else:
                    # fail-fast: respondemos con el fallback sin llamar a la nube
                    return fallback(*argumentos), "FALLBACK (circuito OPEN)"
            if self.estado == Estado.HALF_OPEN:
                if self.pruebas_lanzadas >= self.pruebas_half_open:
                    return fallback(*argumentos), "FALLBACK (HALF_OPEN lleno)"
                self.pruebas_lanzadas += 1
            estado_inicial = self.estado

        # Llamada real a la nube (fuera del lock para no bloquear a otros hilos)
        t0 = time.monotonic()
        try:
            resultado = funcion(*argumentos)
            ok = True
        except Exception:                      # Timeout o error de red = fallo
            resultado = None
            ok = False
        duracion = time.monotonic() - t0
        lenta = duracion > self.duracion_lenta

        with self.lock:
            if estado_inicial == Estado.HALF_OPEN and self.estado == Estado.HALF_OPEN:
                if not ok or lenta:
                    self._abrir()              # Una prueba falla -> vuelve a OPEN
                else:
                    self.pruebas_ok += 1
                    if self.pruebas_ok >= self.pruebas_half_open:
                        self._cerrar()         # 3 pruebas OK -> CLOSED
            elif self.estado == Estado.CLOSED:
                self.ventana.append((ok, lenta))
                if len(self.ventana) >= self.minimo_llamadas and (
                        self.tasa_fallos() >= self.umbral_fallos or
                        self.tasa_lentas() >= self.umbral_lentas):
                    self._abrir()              # Supera umbrales -> OPEN

        if ok:
            return resultado, f"NUBE ({duracion*1000:.0f} ms)"
        return fallback(*argumentos), f"FALLBACK (falló la nube, {duracion*1000:.0f} ms)"


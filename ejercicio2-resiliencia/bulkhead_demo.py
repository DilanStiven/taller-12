# bulkhead_demo.py
# Bulkhead de hilos: un pool independiente por compartimento.
# Demuestra que la IA lenta NO bloquea las alertas críticas.

import threading
import time
from concurrent.futures import ThreadPoolExecutor

# Un pool por compartimento (tabla de la guía)
pool_alertas = ThreadPoolExecutor(max_workers=16, thread_name_prefix="uci-alerta")
pool_telemetria = ThreadPoolExecutor(max_workers=8, thread_name_prefix="telemetria")
pool_ia = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ia-nube")

# Cupo del compartimento IA: 4 en ejecución + 20 en cola
cupo_ia = threading.BoundedSemaphore(4 + 20)


def fallback_local(muestra):
    return f"fallback local({muestra})"


def llamar_ia(muestra):
    time.sleep(2)                    # Simula una nube MUY lenta (WAN degradada)
    return f"ia({muestra})"


def enviar_a_ia(muestra):
    # Si el compartimento está lleno, rechazamos de inmediato (no contagia)
    if not cupo_ia.acquire(blocking=False):
        return fallback_local(muestra)
    fut = pool_ia.submit(llamar_ia, muestra)
    fut.add_done_callback(lambda _: cupo_ia.release())   # Libera el cupo al terminar
    return fut


def procesar_alerta(n):
    return f"ALERTA CRÍTICA {n} atendida"


# --- Prueba: saturamos la IA con 40 peticiones ---
rechazadas = 0
for i in range(40):
    r = enviar_a_ia(i)
    if isinstance(r, str):           # Devolvió fallback = compartimento lleno
        rechazadas += 1
print(f"Peticiones a IA rechazadas (fallback inmediato): {rechazadas} de 40")

# --- Mientras la IA está saturada, las alertas siguen fluyendo ---
t0 = time.monotonic()
futuros = [pool_alertas.submit(procesar_alerta, i) for i in range(5)]
for f in futuros:
    print(f.result())
print(f"Alertas atendidas en {(time.monotonic()-t0)*1000:.1f} ms "
      "(sin esperar a la IA)")

# Cerramos los pools sin esperar a las tareas lentas pendientes
pool_ia.shutdown(wait=False, cancel_futures=True)
pool_alertas.shutdown()
pool_telemetria.shutdown()


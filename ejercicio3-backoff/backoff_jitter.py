# backoff_jitter.py - Sesión 12 Arquitectura de Sistemas Computacionales
# Ejercicio 3: Backoff exponencial con jitter vs. Thundering Herd (10.000 sensores AgroSugar)
import random
from collections import Counter
import matplotlib.pyplot as plt

T_BASE, T_MAX, JITTER, N = 1.0, 30.0, 0.5, 10_000   # s, s, s, sensores
C_GATEWAY = 2_000                                   # capacidad del gateway (TPS)
BUSES, INTERVALO, TOKEN_BUCKET = 500, 10, 1_500     # MetroMIO y Token Bucket de AgroSugar
random.seed(42)


def t_wait(intento, usar_jitter=True):
    """Backoff exponencial con jitter fijo U(0; JITTER)."""
    base = min(T_MAX, T_BASE * (2 ** intento))
    return base + (random.uniform(0, JITTER) if usar_jitter else 0.0)


def t_wait_full_jitter(intento):
    """Full Jitter: espera uniforme en toda la ventana exponencial."""
    return random.uniform(0, min(T_MAX, T_BASE * (2 ** intento)))


def llegadas_ms(variante, intento=1):
    """Instante de llegada (en ms) de cada uno de los N sensores."""
    if variante == "sin":
        f = lambda: t_wait(intento, usar_jitter=False)
    elif variante == "jitter":
        f = lambda: t_wait(intento, usar_jitter=True)
    else:
        f = lambda: t_wait_full_jitter(intento)
    return [int(f() * 1000) for _ in range(N)]


def analizar(titulo, tiempos_ms):
    """Pico por ms y carga por ventanas de 1 s (TPS) frente a la capacidad del gateway."""
    por_ms = Counter(tiempos_ms)
    por_s = Counter(t // 1000 for t in tiempos_ms)      # peticiones por cada segundo
    pico_ms = max(por_ms.values())
    tps_max = max(por_s.values())
    seg_sobre = sum(1 for v in por_s.values() if v > C_GATEWAY)
    estado = "SATURADO" if tps_max > C_GATEWAY else "OK"
    print(f"[{titulo}]")
    print(f"  Pico = {pico_ms} peticiones en 1 ms")
    print(f"  Carga máxima = {tps_max} TPS | segundos sobre {C_GATEWAY} TPS = {seg_sobre}")
    print(f"  Gateway ({C_GATEWAY} TPS): {estado}")
    return {"titulo": titulo, "t": tiempos_ms, "pico": pico_ms, "tps": tps_max,
            "seg": seg_sobre, "estado": estado}


print("=" * 62)
print("EJERCICIO 3 - Backoff Exponencial con Jitter")
print(f"AgroSugar: {N:,} sensores | Gateway: {C_GATEWAY:,} TPS".replace(",", "."))
print("=" * 62)

r_sin = analizar("Sin jitter (reintento 1)", llegadas_ms("sin"))
r_jit = analizar("Jitter fijo U(0; 0,5 s) (reintento 1)", llegadas_ms("jitter"))
r_f1 = analizar("Full Jitter, reintento 1 (ventana 2 s)", llegadas_ms("full", 1))
r_f2 = analizar("Full Jitter, reintento 2 (ventana 4 s)", llegadas_ms("full", 2))
r_f3 = analizar("Full Jitter, reintento 3 (ventana 8 s)", llegadas_ms("full", 3))
r_f4 = analizar("Full Jitter, reintento 4 (ventana 16 s)", llegadas_ms("full", 4))

print("[Tasa media y ventana mínima]")
print(f"  Jitter fijo: N/W = {N}/{JITTER} s = {N / JITTER:.0f} TPS")
print(f"  Full Jitter reintento 1: N/W = {N}/2 s = {N / 2:.0f} TPS")
print(f"  Ventana mínima: W >= N/C = {N}/{C_GATEWAY} = {N / C_GATEWAY:.1f} s")
print("[Carga buses MetroMIO]")
print(f"  {BUSES} buses / {INTERVALO} s = {BUSES / INTERVALO:.1f} TPS")
print(f"  Token Bucket AgroSugar: {TOKEN_BUCKET} TPS")
libres = C_GATEWAY - TOKEN_BUCKET
print(f"  TPS libres para MetroMIO: {libres} (necesita {BUSES / INTERVALO:.1f} TPS) OK")
print("=" * 62)

# --- Gráfica comparativa: carga en TPS (bins de 50 ms) frente a la capacidad del gateway ---
paneles = [(r_sin, (1.5, 2.5)), (r_jit, (1.9, 2.6)), (r_f1, (0, 2)), (r_f3, (0, 8))]
fig, ejes = plt.subplots(2, 2, figsize=(11, 8), sharey=True)
for ax, (r, xlim) in zip(ejes.flat, paneles):
    bins = Counter(t // 50 for t in r["t"])              # peticiones por bin de 50 ms
    xs = [b * 0.05 for b in bins]                        # inicio de cada bin (s)
    tps = [v / 0.05 for v in bins.values()]              # peticiones/bin -> TPS
    color = "red" if r["estado"] == "SATURADO" else "green"
    ax.bar(xs, tps, width=0.05, align="edge", color=color, alpha=0.8)
    ax.axhline(C_GATEWAY, color="blue", linestyle="--", label=f"Capacidad gateway ({C_GATEWAY} TPS)")
    ax.set_yscale("log")
    ax.set_xlim(*xlim)
    pico_tps = f"{max(tps):,.0f}".replace(",", ".")        # separador de miles con punto
    ax.set_title(f"{r['titulo']}\nPico = {pico_tps} TPS (bins de 50 ms)", fontsize=9)
    ax.set_xlabel("Tiempo desde la falla (s)")
    ax.grid(alpha=0.3)
for ax in ejes[:, 0]:
    ax.set_ylabel("Carga (TPS, escala logarítmica)")
ejes[0, 0].legend(fontsize=8, loc="lower left")
fig.suptitle("Ejercicio 3 - Distribución de llegadas de 10.000 sensores AgroSugar")
plt.tight_layout()
plt.savefig("grafica_backoff.png", dpi=150)
plt.show()

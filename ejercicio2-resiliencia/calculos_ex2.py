# calculos_ex2.py
# Calcula el error budget, la disponibilidad en serie vs paralelo
# y la Ley de Little del Ejercicio 2.

SLA = 0.99999                       # 99,999 %
MIN_ANIO = 525_600                  # minutos en un año

# ---------- 2.2 Error budget ----------
U = 1 - SLA                         # Indisponibilidad permitida
print("=== ERROR BUDGET (SLA 99,999 %) ===")
for nombre, minutos in [("Año", 525_600), ("Mes (30d)", 43_200),
                        ("Semana", 10_080), ("Día", 1_440)]:
    permitido = minutos * U         # Minutos de caída permitidos
    print(f"{nombre:<10}: {permitido:.4f} min = {permitido*60:.2f} s")

# ---------- 2.3 Supuestos de disponibilidad (documentarlos en el informe) ----------
A_L = 0.999995                      # Núcleo local UCI con redundancia
A_W = 0.999                         # WAN
A_C = 0.9995                        # IA en la nube
A_F = 0.9999                        # Fallback local

# (a) SIN Circuit Breaker: todo en SERIE
A_remota = A_W * A_C
A_serie = A_L * A_remota
caida_a = (1 - A_serie) * MIN_ANIO
print("\n=== (a) SIN Circuit Breaker (serie) ===")
print(f"A_remota = {A_remota:.7f}")
print(f"A_serie  = {A_serie:.6f}")
print(f"Caída    = {caida_a:.1f} min/año = {caida_a/60:.1f} h/año ->",
      "SÍ cumple" if A_serie >= SLA else "NO cumple")

# (b) CON Circuit Breaker + Fallback: remota y fallback en PARALELO
A_func = 1 - (1 - A_remota) * (1 - A_F)
A_total = A_L * A_func
caida_b = (1 - A_total) * MIN_ANIO
print("\n=== (b) CON Circuit Breaker + Fallback (paralelo) ===")
print(f"A_func  = {A_func:.8f}")
print(f"A_total = {A_total:.7f}")
print(f"Caída   = {caida_b:.2f} min/año ->",
      "SÍ cumple" if A_total >= SLA else "NO cumple")

# ---------- Verifique: ¿y si A_L = 0.99999 exacto? ----------
A_total_v = 0.99999 * A_func
print(f"\nVerifique: 0,99999 x A_func = {A_total_v:.8f} ->",
      "cumple" if A_total_v >= SLA else "NO cumple (el núcleo local necesita redundancia)")

# ---------- Ley de Little: L = lambda * W ----------
lam = 100                           # consultas/s a la IA
W_timeout = 5                       # s de espera con WAN caída (timeout por defecto)
W_open = 0.00005                    # s (0,05 ms) con el circuito OPEN
print("\n=== LEY DE LITTLE (L = λ·W) ===")
print(f"Sin CB : L = {lam} x {W_timeout} = {lam*W_timeout:.0f} hilos bloqueados")
print(f"Con OPEN: L = {lam} x {W_open} = {lam*W_open:.3f} hilos")


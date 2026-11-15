# Ejercicio 2 · Patrones de resiliencia y máquina de estados

Circuit Breaker, cálculo de SLA y Bulkhead para el monitoreo cardiaco de la UCI de HospitValle.

## Archivos

| Archivo | Qué hace |
|---|---|
| `ia_nube_simulada.py` | Servidor que simula la IA en la nube, con latencia configurable (`--latencia`) |
| `circuit_breaker.py` | Circuit Breaker (CLOSED, OPEN, HALF-OPEN) con los parámetros del informe |
| `cliente_uci.py` | Monitor de la UCI que consulta la IA a través del Circuit Breaker |
| `calculos_ex2.py` | Error budget, disponibilidad serie vs paralelo y Ley de Little |
| `bulkhead_demo.py` | Bulkhead de hilos: la IA saturada no bloquea las alertas críticas |
| `bulkhead_uci.yaml` | Bulkhead por recursos en Kubernetes (PriorityClass y límites de CPU) |

## Cómo ejecutarlo (Python 3.10 o superior)

Terminal 1: `python ia_nube_simulada.py --latencia 0`
Terminal 2: `python cliente_uci.py`

Cálculos: `python calculos_ex2.py`
Bulkhead de hilos: `python bulkhead_demo.py`
Validar el YAML: `kubectl apply --dry-run=client --validate=false -f bulkhead_uci.yaml`

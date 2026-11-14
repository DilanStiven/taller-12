# Ejercicio 1 - Trazabilidad distribuida y propagacion de contexto (W3C Trace Context)

Implementacion de trazabilidad distribuida con **OpenTelemetry (Python)** para el flujo de telemetria de **MetroMIO-IoT** (`Bus MIO -> Broker MQTT K3s -> API Gateway mTLS -> Ingesta Service -> TimescaleDB`).

## Archivos incluidos
- `traza_metromio.py`: Simulacion secuencial de los 4 saltos con propagacion manual (`extract` / `inject`) del encabezado W3C `traceparent` y medicion de latencias del Root Span.
- `ingesta_flask.py`: Microservicio REST en Flask (`POST /telemetria`) con aislamiento multitenant (`service.namespace: metromio`), creacion de span hijo `SpanKind.CLIENT`, inyeccion de `traceparent` en comentario SQL y correlacion de logs con `trace_id`.
- `requirements.txt`: Dependencias del proyecto.

## Ejecucion rapida (Windows PowerShell)

```powershell
python -m venv venv-otel
venv-otel\Scripts\activate
pip install -r requirements.txt
python traza_metromio.py
```

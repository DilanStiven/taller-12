# Ejercicio 1 · Trazabilidad distribuida y propagación de contexto (W3C Trace Context)

Implementación de trazabilidad distribuida con **OpenTelemetry (Python)** para el flujo de telemetría de **MetroMIO-IoT**:

`Bus MIO -> Broker MQTT K3s -> API Gateway mTLS -> Ingesta Service -> TimescaleDB`

---

## Archivos incluidos

- `traza_metromio.py`: simulación secuencial de los 4 saltos con propagación manual (`extract` / `inject`) del encabezado W3C `traceparent` y medición de latencias del Root Span.
- `ingesta_flask.py`: microservicio REST en Flask (`POST /telemetria`) con aislamiento multitenant (`service.namespace: metromio`), creación de span hijo `SpanKind.CLIENT`, inyección de `traceparent` en comentario SQL y correlación de logs con `trace_id`.
- `requirements.txt`: dependencias del proyecto.

---

## Ejecución rápida (Windows PowerShell)

Desde esta carpeta:

```powershell
python -m venv venv-otel
venv-otel\Scripts\activate
pip install -r requirements.txt
python traza_metromio.py
```

En Linux o Mac, el entorno virtual se activa con `source venv-otel/bin/activate`.

---

## Servicio Flask de ingesta

**Terminal 1** (levantar el servicio, con el entorno virtual activado):

```powershell
python ingesta_flask.py
```

**Terminal 2** (enviar una petición de prueba con un `traceparent` entrante):

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:5000/telemetria" -Method Post -Headers @{ "Content-Type" = "application/json"; "traceparent" = "00-5e3ea00eb9434cb7f9d28e116c567861-f65c907a89acc6db-03" } -Body '{"bus_id": "MIO-T31-0457", "lat": 3.4516, "lon": -76.5320}'
```

La respuesta devuelve el mismo `trace_id` del `traceparent` enviado (`5e3ea00eb9434cb7f9d28e116c567861`). En la Terminal 1 se ven el SQL con el comentario `traceparent`, el span hijo `timescaledb.insert`, el log correlacionado y el span servidor `ingesta.procesar`.

La base de datos se simula: el servicio imprime el SQL que ejecutaría, sin requerir un PostgreSQL desplegado.

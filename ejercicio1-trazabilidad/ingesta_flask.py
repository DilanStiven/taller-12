# ingesta_flask.py - Microservicio de ingesta con propagación W3C y log correlacionado
from flask import Flask, request
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.propagate import extract, inject
import logging

# Configurar OpenTelemetry
provider = TracerProvider(resource=Resource.create({
    "service.name": "ingesta-service",
    "service.namespace": "metromio"
}))
provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(provider)

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
tracer = trace.get_tracer("ingesta-service")

@app.post("/telemetria")
def recibir():
    # 1. Extraer traceparent entrante (normalizando llaves a minúsculas para Flask)
    encabezados = {k.lower(): v for k, v in request.headers.items()}
    ctx = extract(encabezados)

    with tracer.start_as_current_span("ingesta.procesar", context=ctx,
                                      kind=trace.SpanKind.SERVER) as span:
        d = request.json
        trace_id = format(span.get_span_context().trace_id, "032x")
        span.set_attribute("bus.id", d["bus_id"])
        span.set_attribute("tenant", "metromio")

        # 2. Span hijo hacia TimescaleDB con inyección en comentario SQL
        with tracer.start_as_current_span("timescaledb.insert",
                                          kind=trace.SpanKind.CLIENT) as db_span:
            db_span.set_attribute("db.system", "postgresql")
            carrier = {}
            inject(carrier)
            sql = f"/*traceparent='{carrier['traceparent']}'*/ INSERT INTO telemetria VALUES (%s, %s, %s)"
            print(f">> SQL ejecutado: {sql} | Params: ({d['bus_id']}, {d['lat']}, {d['lon']})")

        app.logger.info({"msg": "guardada", "trace_id": trace_id, "bus_id": d["bus_id"]})
        return {"status": "ok", "trace_id": trace_id}, 201

if __name__ == "__main__":
    app.run(port=5000)
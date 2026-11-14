# traza_metromio.py
# Simula los 4 saltos de MetroMIO-IoT y propaga el contexto W3C (traceparent).
# Cadena: Root -> Salto1 -> Salto2 -> Salto3 -> Salto4
import time
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.propagate import inject, extract

# --- Configuración de OpenTelemetry: los spans se imprimen en la consola ---
provider = TracerProvider(resource=Resource.create({"service.name": "metromio-ingesta"}))
provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("metromio.lab")


def salto(nombre, headers_entrantes, segundos, atributos=None):
    """Un salto de la arquitectura:
    1) EXTRAE el traceparent que llega del salto anterior,
    2) crea su span como hijo de ese contexto,
    3) INYECTA el nuevo traceparent para el siguiente salto.
    """
    ctx = extract(headers_entrantes)                      # 1) extraer
    with tracer.start_as_current_span(nombre, context=ctx) as span:
        for k, v in (atributos or {}).items():
            span.set_attribute(k, v)
        time.sleep(segundos)                              # trabajo simulado
        headers_salida = {}
        inject(headers_salida)                            # 3) inyectar
    print(f">> {nombre} envió traceparent:", headers_salida["traceparent"])
    return headers_salida


# --- Root Span: el bus crea el TraceID ---
with tracer.start_as_current_span("root.bus-telemetria") as root:
    root.set_attribute("bus.id", "MIO-T31-0457")
    h = {}
    inject(h)
    print(">> root envió traceparent:", h["traceparent"])

    h = salto("salto1.edge-mqtt-k3s", h, 0.012)                                   # 12 ms
    h = salto("salto2.api-gateway-mtls", h, 0.008)                                # 8 ms
    h = salto("salto3.ingesta-service", h, 0.045)                                 # 45 ms
    h = salto("salto4.timescaledb.insert", h, 0.003,
              {"db.system": "postgresql", "db.operation": "INSERT"})              # 3 ms

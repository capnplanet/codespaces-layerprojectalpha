from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def setup_tracer(service_name: str, otlp_endpoint: str) -> None:
    resource = Resource(attributes={SERVICE_NAME: service_name})
    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True))
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

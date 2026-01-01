from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter("api_requests_total", "Total API requests", ["endpoint", "status"])
REQUEST_LATENCY = Histogram("api_request_latency_ms", "Latency in ms", ["endpoint"])

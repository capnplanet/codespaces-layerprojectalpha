PYTHON=python
PIP=pip

.PHONY: format lint typecheck test up down migrate seed sbom perf-baseline perf-assert

install:
	$(PIP) install -e .[dev]

format:
	black app tests
	ruff check --fix app tests

lint:
	ruff check app tests
	black --check app tests

typecheck:
	mypy app

default: test

test:
	pytest

up:
	docker-compose up --build

down:
	docker-compose down

migrate:
	alembic upgrade head

seed:
	$(PYTHON) scripts/seed.py

sbom:
	$(PYTHON) -m pip install cyclonedx-bom && cyclonedx-py -o sbom.json

perf-baseline:
	$(PYTHON) scripts/perf_baseline.py --api-url http://localhost:8000 --requests 100 --concurrency 2 --requests-per-second 0.8 --role admin

perf-assert:
	$(PYTHON) scripts/perf_baseline.py --api-url http://localhost:8000 --requests 100 --concurrency 2 --requests-per-second 0.8 --role admin --max-p95-latency-ms 2000 --min-throughput-rps 0.5 --max-avg-cost-units 40 --require-policy-compliance

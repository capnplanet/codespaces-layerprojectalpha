PYTHON=python
PIP=pip

.PHONY: format lint typecheck test up down migrate seed sbom

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

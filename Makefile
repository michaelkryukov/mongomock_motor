.PHONY: all

all: check test

check:
	python3 -m ruff check mongomock_motor/ tests/ && \
	python3 -m ruff format --check mongomock_motor/ tests/

format:
	python3 -m ruff check --fix mongomock_motor/ tests/ && \
	python3 -m ruff format mongomock_motor/ tests/

test:
	ENVIRONMENT=test python3 -m pytest tests/

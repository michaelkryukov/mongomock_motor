.PHONY: all

all: check test

check:
	poetry run python -m ruff check mongomock_motor/ tests/ && \
	poetry run python -m ruff format --check mongomock_motor/ tests/

format:
	poetry run python -m ruff check --fix mongomock_motor/ tests/ && \
	poetry run python -m ruff format mongomock_motor/ tests/

test:
	poetry run python -m pytest tests/

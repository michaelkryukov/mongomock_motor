.PHONY: all check format test

all: check test

check:
	poetry run ruff check mongomock_motor tests && \
	poetry run ruff format --check mongomock_motor tests && \
	poetry run pyright mongomock_motor tests


format:
	poetry run ruff check --fix mongomock_motor tests && \
	poetry run ruff format mongomock_motor tests

test:
	poetry run pytest tests

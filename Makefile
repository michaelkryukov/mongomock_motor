.PHONY: all

all: lint test

lint:
	python3 -c "import flake8" || python3 -m pip install flake8 flake8-quotes
	flake8 mongomock_motor/ --count --select=E9,F63,F7,F82 --show-source --statistics
    flake8 mongomock_motor/ --count --max-complexity=10 --max-line-length=127 --statistics

test:
	python3 -c "import pytest" || python3 -m pip install pytest
	python3 -c "import requests" || python3 -m pip install requests
	ENVIRONMENT=test python3 -m pytest tests/

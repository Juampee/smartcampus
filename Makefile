.PHONY: hooks install lint test unit integration run docker-up
PYTHON ?= python

hooks:
	sh scripts/install-hooks.sh

install:
	$(PYTHON) -m pip install -r requirements.txt

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .

unit:
	$(PYTHON) -m pytest -m unit

integration:
	$(PYTHON) -m pytest -m integration

test:
	$(PYTHON) -m pytest

run:
	$(PYTHON) -m app.main

docker-up:
	docker compose up --build -d

.PHONY: help backend-venv backend-install backend-test backend-run backend-migrate

help:
	@echo "Available targets:"
	@echo "  make backend-venv     Create backend virtual environment"
	@echo "  make backend-install  Install backend dependencies"
	@echo "  make backend-test     Run backend test suite"
	@echo "  make backend-run      Run backend API in dev mode"
	@echo "  make backend-migrate  Run Alembic migrations"

backend-venv:
	python3 -m venv backend/.venv

backend-install:
	backend/.venv/bin/python -m pip install --upgrade pip
	backend/.venv/bin/python -m pip install -r backend/requirements.txt

backend-test:
	cd backend && .venv/bin/python -m pytest -q

backend-run:
	cd backend && .venv/bin/python -m uvicorn app.main:app --reload

backend-migrate:
	cd backend && .venv/bin/python -m alembic upgrade head

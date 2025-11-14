# Makefile for FastAPI Middleware project

.PHONY: help install run test lint format clean docker-up docker-down migrate

help:
	@echo "Available commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make run           - Run development server"
	@echo "  make test          - Run tests"
	@echo "  make test-unit     - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make lint          - Run linting"
	@echo "  make format        - Format code"
	@echo "  make migrate       - Run database migrations"
	@echo "  make migrate-create - Create new migration"
	@echo "  make docker-up     - Start Docker containers"
	@echo "  make docker-down   - Stop Docker containers"
	@echo "  make docker-logs   - View Docker logs"
	@echo "  make clean         - Clean temporary files"

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v --cov=app --cov-report=html

test-unit:
	pytest tests/unit/ -v -m unit

test-integration:
	pytest tests/integration/ -v -m integration

lint:
	ruff check app/
	mypy app/

format:
	black app/ tests/
	ruff --fix app/

migrate:
	alembic upgrade head

migrate-create:
	@read -p "Enter migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

migrate-downgrade:
	alembic downgrade -1

docker-up:
	docker-compose -f docker/docker-compose.yml up -d

docker-down:
	docker-compose -f docker/docker-compose.yml down

docker-logs:
	docker-compose -f docker/docker-compose.yml logs -f api

docker-build:
	docker-compose -f docker/docker-compose.yml build

docker-restart:
	docker-compose -f docker/docker-compose.yml restart

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .coverage htmlcov/
	rm -rf .mypy_cache
	rm -rf .ruff_cache

db-reset:
	@echo "WARNING: This will delete all data!"
	@read -p "Are you sure? [y/N] " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		alembic downgrade base; \
		alembic upgrade head; \
		echo "Database reset complete"; \
	else \
		echo "Cancelled"; \
	fi

shell:
	python -m IPython

setup:
	@echo "Setting up project..."
	cp .env.example .env
	@echo "Created .env file. Please update it with your configuration."
	mkdir -p logs
	@echo "Created logs directory"
	@echo "Setup complete! Run 'make install' to install dependencies."

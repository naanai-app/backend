# Makefile for Place Recommendation API

.PHONY: help build up down logs shell db-init db-reset db-check db-seed create-admin dev clean

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build Docker images
	docker-compose build

up: ## Start all services
	docker-compose up -d

down: ## Stop all services
	docker-compose down

logs: ## Show logs from all services
	docker-compose logs -f

logs-app: ## Show logs from app service only
	docker-compose logs -f app

shell: ## Open shell in app container
	docker-compose exec app bash

db-check: ## Check database health
	docker-compose exec app python scripts/check_db.py

db-seed: ## Seed initial data
	docker-compose exec app python scripts/seed_data.py

create-admin: ## Create admin user
	docker-compose exec app python scripts/create_admin.py

dev: ## Start development server locally
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

test: ## Run tests
	pytest

clean: ## Clean up Docker resources
	docker-compose down -v
	docker system prune -f

restart: ## Restart all services
	docker-compose restart

rebuild: ## Rebuild and restart services
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d

# Database shortcuts
check: db-check ## Alias for db-check
seed: db-seed ## Alias for db-seed
admin: create-admin ## Alias for create-admin

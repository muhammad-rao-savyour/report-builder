.PHONY: up down logs test sh reset

up:      ## start everything locally
	docker compose up --build

down:    ## stop everything
	docker compose down

logs:    ## follow the worker logs
	docker compose logs -f worker

test:    ## run the test suite inside the container
	docker compose run --rm --no-deps api pytest -q

sh:      ## shell inside the api container
	docker compose run --rm --no-deps api bash

reset:   ## wipe the database and storage
	docker compose down -v

itest:   ## run integration tests against the real running system
	docker compose up -d --build
	docker compose run --rm -e S3_PUBLIC_ENDPOINT=http://minio:9000 \
		api python -m pytest tests_integration

lint:    ## check style and common mistakes
	docker compose run --rm --no-deps api ruff check .

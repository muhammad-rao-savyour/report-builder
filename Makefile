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

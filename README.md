# Report Builder

A small project skeleton: CRUD + large file upload + background processing.
Built so the same code runs on your laptop and on AWS with no changes.

## Run it locally

    cp .env.example .env
    docker compose up --build

Then open http://localhost:8000/docs

If a port is already used by another project, change it in `.env` (the
`*_PORT` lines at the top) and run `docker compose up` again. If you change
`MINIO_PORT`, update `S3_PUBLIC_ENDPOINT` to the same port.

Other useful addresses while it runs:

| Address | What it is | Login |
|---|---|---|
| http://localhost:8000/docs | The API, clickable | - |
| http://localhost:15672 | RabbitMQ, watch the queue | guest / guest |
| http://localhost:9001 | MinIO, your fake S3 | minioadmin / minioadmin |

## Run the tests

    make test

## Try the upload flow

1. `POST /uploads` with `{"filename": "test.csv"}` -> you get an `upload_url`
2. `PUT` your CSV file to that URL (curl: `curl -X PUT --upload-file test.csv "<url>"`)
3. `POST /uploads/{id}/complete` -> the job goes on the queue
4. `GET /uploads/{id}` -> watch status change to `done` and see the row count

Watch `docker compose logs -f worker` while step 4 runs.

## The shape of the project

    backend/app/config.py   reads env vars, nothing else
    backend/app/db.py       database connection pool
    backend/app/models.py   tables
    backend/app/schemas.py  request/response shapes
    backend/app/storage.py  S3 (MinIO locally, real S3 on AWS)
    backend/app/tasks.py    background jobs
    backend/app/main.py     API routes

One Docker image runs both the API and the worker. Only the start command
differs -- see the `api` and `worker` services in docker-compose.yml.

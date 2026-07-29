"""Integration tests: nothing is faked.

These talk to the REAL Postgres and the REAL object storage running in
docker compose. That is the whole point -- unit tests prove your logic is
right, integration tests prove your logic works against actual systems.

One shortcut: we tell Celery to run tasks immediately in this process instead
of sending them to RabbitMQ. That way we do not need a live worker to test the
task's logic. Testing the real queue handover is the next level up.
"""
import pytest
from app.celery_app import celery_app
from app.config import settings
from app.db import Base, engine
from app.main import app
from app.storage import internal
from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def real_system():
    Base.metadata.create_all(bind=engine)

    try:
        internal.create_bucket(Bucket=settings.s3_bucket)
    except Exception:
        pass  # already exists

    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    yield


@pytest.fixture
def client():
    return TestClient(app)

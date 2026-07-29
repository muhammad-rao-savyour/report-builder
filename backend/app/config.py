"""All configuration comes from environment variables.

This is the single most important rule for scalability: the code never knows
whether it is running on your laptop or on twenty EC2 servers. The environment
tells it. That is why the same Docker image works everywhere.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://app:app@postgres:5432/app"
    broker_url: str = "amqp://guest:guest@rabbitmq:5672//"

    s3_bucket: str = "uploads"
    # Empty string means "use the real AWS S3". Set locally to point at MinIO.
    s3_endpoint: str = ""
    s3_public_endpoint: str = ""

    aws_region: str = "us-east-1"
    # Local convenience only. On AWS this stays false and you run
    # migrations as a deliberate step, so ten servers booting at once do
    # not all try to change the schema at the same moment.
    create_tables: bool = False
    csv_progress_every: int = 50_000


settings = Settings()

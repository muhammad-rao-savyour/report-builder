# Stage 1: build wheels. Compilers live here and never reach the final image.
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# Stage 2: the image you actually ship. Small, no build tools.
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels

COPY app ./app
COPY tests ./tests
COPY pytest.ini .

# Never run as root.
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Default = API. The worker overrides this with its own command.
# ONE IMAGE, TWO COMMANDS.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

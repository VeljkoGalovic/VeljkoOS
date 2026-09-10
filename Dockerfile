FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencies land in their own layer so app edits do not trigger a reinstall.
# No build toolchain is needed: asyncpg ships manylinux wheels.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini entrypoint.sh ./
COPY alembic ./alembic
COPY app ./app

RUN chmod +x entrypoint.sh \
    && useradd --create-home --uid 1000 veljko \
    && chown -R veljko:veljko /app
USER veljko

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]

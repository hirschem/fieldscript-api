FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY README.md ./
EXPOSE 8000
ENV PORT=8000
COPY alembic.ini ./
COPY alembic ./alembic
COPY scripts ./scripts
CMD ["sh", "-c", "python scripts/migrate.py && uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]

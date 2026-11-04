FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd -m -u 10001 app && mkdir /data && chown app:app /data
COPY backend/ /app/
ENV DATABASE_PATH=/data/finpilot.db PYTHONUNBUFFERED=1
USER app
EXPOSE 8000
CMD ["uvicorn", "finpilot.api:app", "--host", "0.0.0.0", "--port", "8000"]

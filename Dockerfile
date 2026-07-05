FROM node:22-slim AS frontend

WORKDIR /app/apps/frontend
COPY apps/frontend/package*.json ./
RUN npm ci
COPY apps/frontend ./
RUN npm run build

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY apps/backend/requirements.txt ./apps/backend/requirements.txt
RUN pip install --no-cache-dir -r ./apps/backend/requirements.txt

COPY apps/backend ./apps/backend
COPY --from=frontend /app/apps/frontend/dist ./apps/frontend/dist
RUN mkdir -p ./apps/backend/data

WORKDIR /app/apps/backend
EXPOSE 10000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]

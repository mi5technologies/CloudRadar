# Stage 1: build Vue frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist
RUN pip install -e .
EXPOSE 8000
ENV CSPM_RULES_DIR=/app/cspm/rules
ENV CSPM_SNAPSHOTS_DIR=/data/snapshots
VOLUME ["/data"]
CMD ["python", "-m", "cspm.cli", "ui", "--host", "0.0.0.0", "--port", "8000"]

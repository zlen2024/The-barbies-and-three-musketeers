# Stage 1: Build the frontend
FROM node:18-alpine as build
WORKDIR /app/frontend

# Install dependencies
COPY frontend/package*.json ./
RUN npm ci

# Copy source code and build
COPY frontend/ ./
RUN npm run build

# Stage 2: Set up the backend
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies for pyodbc and Azure SQL
# Need gnupg instead of gnupg2 for newer debian 11/12
RUN apt-get update && apt-get install -y curl gnupg apt-transport-https unixodbc-dev && \
    curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg && \
    curl -fsSL https://packages.microsoft.com/config/debian/12/prod.list | tee /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql18 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY app.py models.py seed_data.py azure_forecast.py scheduler.py azure_margin_agent.py azure_margin_simulator.py ./
# Copy built frontend assets
# The build output is usually in `dist` relative to the frontend root.
# So from Stage 1 (`/app/frontend/dist`) to Stage 2 (`/app/frontend/dist`).
# We need to create the directory first if COPY doesn't do it automatically (it does).
COPY --from=build /app/frontend/dist ./frontend/dist

# Expose port (Fly.io uses 8080 by default)
EXPOSE 8080

# Environment variables
ENV FLASK_APP=app.py
ENV PORT=8080

# Run command: Start gunicorn
# Use 1 worker to prevent SQLite locking issues, and multiple threads for concurrency.
# Add logging to stdout/stderr for Fly.io log capture.
CMD ["sh", "-c", "gunicorn --worker-class=geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 --timeout=120 --access-logfile - --error-logfile - --bind=0.0.0.0:8080 app:app"]

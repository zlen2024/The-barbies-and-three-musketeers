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

# Install system dependencies (none obvious, but good to have minimal base)
# We can add `RUN apt-get update && apt-get install -y ...` if needed.

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY app.py models.py seed_data.py azure_forecast.py scheduler.py ./
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

# Run command: Seed database and start gunicorn
# Use 1 worker to prevent SQLite locking issues, and multiple threads for concurrency.
# Add logging to stdout/stderr for Fly.io log capture.
CMD ["sh", "-c", "python seed_data.py && gunicorn --workers=1 --threads=4 --timeout=120 --access-logfile - --error-logfile - --bind=0.0.0.0:8080 app:app"]

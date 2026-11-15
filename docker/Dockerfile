FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY ml/ ./ml/
COPY mlops/ ./mlops/
COPY documents/ ./documents/

# Create log directory
RUN mkdir -p /app/backend/logs

ENV FLASK_ENV=production
ENV PYTHONPATH=/app

EXPOSE 5000

CMD ["python", "backend/run.py"]

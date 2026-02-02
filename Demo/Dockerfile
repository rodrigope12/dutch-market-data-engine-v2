# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Stage 2: Runner
FROM python:3.11-slim

# Create a non-root user for security (The Vault requirement)
RUN groupadd -r axiom && useradd -r -g axiom axiom

WORKDIR /app

# Install runtime dependencies
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache /wheels/*

# Copy Application Code
COPY . .

# Change ownership to non-root user
RUN chown -R axiom:axiom /app

# Switch to non-root user
USER axiom

# Expose Streamlit port
EXPOSE 8501

# Healthcheck
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Entrypoint
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]

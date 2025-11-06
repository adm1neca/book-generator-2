# Start from official Langflow image
FROM langflowai/langflow:latest

# Make sure we can install OS packages if Pillow needs system libs
USER root
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

# Ensure pip exists for the runtime python and install deps
RUN python -m ensurepip --upgrade || true \
 && python -m pip install --upgrade pip setuptools wheel

# Copy requirements first to leverage Docker layer cache
COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install --no-cache-dir -r /tmp/requirements.txt

# --- Add your files ---
# Components: custom Langflow nodes (e.g., Render Booklet)
COPY components /app/components
# Workdir: your renderer, outputs live here (/app/workdir/out)
COPY workdir /app/workdir

# Optional: create output dir now (prevents first-run surprises)
RUN mkdir -p /app/workdir/out
RUN mkdir -p /app/scripts
COPY scripts /app/scripts
# Activity generator script
# COPY scripts/activity_generator.py /app/activity_generator.py

# Environment: tell Langflow where to find your components
ENV LANGFLOW_COMPONENTS_PATH=/app/components
ENV PYTHONUNBUFFERED=1
# Ensure our in-repo modules (scripts, etc.) are importable without manual sys.path tweaks
ENV PYTHONPATH="/app:/app/scripts${PYTHONPATH:+:${PYTHONPATH}}"

# Drop back to the non-root user used by the base image
USER 1000:1000
WORKDIR /app

EXPOSE 7860
CMD ["langflow", "run", "--host", "0.0.0.0", "--port", "7860"]

# FDA Adverse Event Reporter — Shiny for Python
# Based on 04_deployment/digitalocean/shinypy/Dockerfile

FROM python:3.12-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app and API client
COPY app.py .
COPY api_client.py .

# Optional: copy FDA.env at build time (or mount at run time)
# COPY FDA.env . 

EXPOSE 8000
CMD ["shiny", "run", "app.py", "--host", "0.0.0.0", "--port", "8000"]

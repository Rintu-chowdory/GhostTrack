FROM python:3.12-slim

# Run as a non-root user (container security best practice)
RUN useradd --create-home --shell /bin/bash ghost
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY GhostTR.py .

USER ghost

# GhostTrack is an interactive menu tool — keep stdin open
ENTRYPOINT ["python3", "-u", "GhostTR.py"]

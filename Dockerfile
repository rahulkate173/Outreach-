# Cold Outreach Engine (SMB 02) — runs with Ollama in another container
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend ./backend
COPY static ./static
COPY run.py ./
COPY scripts ./scripts

ENV OLLAMA_HOST=http://ollama:11434
ENV OLLAMA_MODEL=phi3:mini
ENV PYTHONPATH=/app
EXPOSE 8000

# Wait for Ollama, pull model from web, then start server
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]

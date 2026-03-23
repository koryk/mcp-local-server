FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY birdnet/ ./birdnet/
COPY data/ ./data/
COPY server.py .

ENV MCP_TRANSPORT=http
ENV MCP_HTTP_PORT=8000
ENV MCP_HTTP_HOST=0.0.0.0

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

LABEL org.opencontainers.image.title="mcp-birdnet-pi-server" \
      org.opencontainers.image.description="MCP server for BirdNET-Pi bird detection data" \
      org.opencontainers.image.version="2.0.0"

ENTRYPOINT ["python", "server.py"]

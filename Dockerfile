FROM python:3.12-slim

WORKDIR /app

# Install dependencies first so code changes don't bust the layer cache.
COPY pyproject.toml README.md ./
COPY hone ./hone
RUN pip install --no-cache-dir ".[web]"

# Public-deployment defaults: never fall back to server-side Alpaca keys.
# Override HONE_PUBLIC=0 for a private deployment that uses env keys.
ENV HONE_PUBLIC=1 \
    HOST=0.0.0.0 \
    PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s \
  CMD python -c "import urllib.request,os; urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/api/health')" || exit 1

CMD ["python", "-m", "hone", "serve"]

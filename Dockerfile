FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

COPY pyproject.toml .
RUN uv sync --frozen

COPY src/ ./src/

CMD ["uv", "run", "src/monitor.py"]

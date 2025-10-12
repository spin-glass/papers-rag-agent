# syntax=docker/dockerfile:1.7

FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc g++ curl && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# 依存関係
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# アプリコード
COPY src/ ./src/
ENV PYTHONPATH=/app/src

# Cloud Run の PORT
ENV PORT=8000

# エントリ：あなたの Chainlit アプリ
CMD ["sh", "-lc", ". .venv/bin/activate && chainlit run src/ui/app.py --host 0.0.0.0 --port ${PORT}"]

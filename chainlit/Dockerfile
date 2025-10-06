# syntax=docker/dockerfile:1.7
ARG TARGETPLATFORM
FROM --platform=$TARGETPLATFORM python:3.13-slim

WORKDIR /app

# 基本ツール
RUN apt-get update && apt-get install -y gcc g++ curl && rm -rf /var/lib/apt/lists/*

# uv インストール
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# 依存関係（リポジトリ直下のファルを想定）
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY src/ ./src/
ENV PYTHONPATH=/app/src

COPY chainlit/ ./chainlit/

# Cloud Run の PORT に合わせる（デフォルト 8000）
ENV PORT=8000

CMD ["sh", "-lc", ". .venv/bin/activate && chainlit run src/ui/app.py --host 0.0.0.0 --port ${PORT}"]

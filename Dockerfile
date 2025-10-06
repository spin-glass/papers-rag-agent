# ARM環境対応のため、プラットフォームを明示的に指定
FROM --platform=linux/amd64 python:3.13-slim

# 作業ディレクトリを設定
WORKDIR /app

# システムの依存関係をインストール
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# uvをインストール
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# pyproject.tomlとuv.lockをコピーして依存関係をインストール
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# uv仮想環境をアクティベートするための環境変数を設定
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src:$PYTHONPATH"

# アプリケーションコードをコピー
COPY src/ ./src/

# Cloud RunのPORT環境変数に対応（デフォルト8000）
# Cloud Runは通常8080を設定するが、エントリーポイントで動的に処理
EXPOSE 8000 8080

# 環境変数を設定
# PORT環境変数はCloud Runが動的に設定（通常8080）

# エントリーポイントスクリプトでCloud RunのPORT環境変数に対応
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# アプリケーションを起動
ENTRYPOINT ["/docker-entrypoint.sh"]

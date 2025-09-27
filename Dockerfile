# ARM環境対応のため、プラットフォームを明示的に指定
FROM --platform=linux/amd64 python:3.13-slim

# 作業ディレクトリを設定
WORKDIR /app

# システムの依存関係をインストール
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# requirements.txtをコピーして依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY src/ ./src/
COPY chainlit.md .
COPY .chainlit/ ./.chainlit/

# ポート8000を公開（Chainlitのデフォルトポート）
EXPOSE 8000

# 環境変数を設定
ENV CHAINLIT_HOST=0.0.0.0
ENV CHAINLIT_PORT=8000

# アプリケーションを起動
CMD ["chainlit", "run", "src/ui/app.py", "--host", "0.0.0.0", "--port", "8000"]

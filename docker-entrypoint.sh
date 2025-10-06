#!/bin/bash
set -e

# 環境変数の確認とデバッグ出力
echo "=== Environment Debug ==="
echo "Original PORT env var: ${PORT:-'not set'}"
echo "All env vars containing PORT:"
env | grep -i port || echo "No PORT variables found"
echo "Python version: $(python --version 2>&1 || echo 'Python not found')"
echo "Current directory: $(pwd)"
echo "Available files:"
ls -la src/api/ || echo "src/api directory not found"

# Cloud RunのPORT環境変数を使用するか、デフォルト8080を使用
FASTAPI_PORT=${PORT:-8080}

echo "=== Starting FastAPI Application ==="
echo "🚀 Application: Papers RAG Agent API"
echo "📍 Host: 0.0.0.0"
echo "🔌 Port: $FASTAPI_PORT"
echo "🔧 Environment: Production"

# 最終確認
echo "=== Final Configuration ==="
echo "PORT: $FASTAPI_PORT"
echo "Command: uvicorn src.api.main:app --host 0.0.0.0 --port $FASTAPI_PORT"

# uv仮想環境をアクティベート
echo "=== Activating uv virtual environment ==="
source /app/.venv/bin/activate || echo "❌ Failed to activate virtual environment"

# Python環境とモジュールの確認
echo "=== Python Environment Check ==="
python -c "import sys; print('Python executable:', sys.executable)" || echo "❌ Python import test failed"
python -c "import fastapi; print('✅ FastAPI version:', fastapi.__version__)" || echo "❌ FastAPI import failed"
python -c "import uvicorn; print('✅ Uvicorn version:', uvicorn.__version__)" || echo "❌ Uvicorn import failed"
python -c "import src.api.main; print('✅ API module import successful')" || echo "❌ API module import failed"

# ヘルスチェック用の簡単なログ出力
echo "✅ Container is ready to receive requests on 0.0.0.0:$FASTAPI_PORT"

# 最終的なポート確認
echo "=== Final Port Verification ==="
echo "Cloud Run PORT env var: ${PORT:-'not set'}"
echo "Resolved FASTAPI_PORT: $FASTAPI_PORT"
echo "Will bind to: 0.0.0.0:$FASTAPI_PORT"

# FastAPIアプリケーションを起動（ポート番号を明示的に指定）
echo "🚀 Starting FastAPI with command: uvicorn src.api.main:app --host 0.0.0.0 --port $FASTAPI_PORT"
echo "🔍 Verification: FastAPI should listen on 0.0.0.0:$FASTAPI_PORT"

# 起動直前に最終確認
if [ -z "$FASTAPI_PORT" ]; then
    echo "❌ FATAL: FASTAPI_PORT is empty!"
    exit 1
fi

exec uvicorn src.api.main:app --host 0.0.0.0 --port $FASTAPI_PORT

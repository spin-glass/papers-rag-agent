#!/bin/bash
set -e

# Cloud RunのPORT環境変数を使用するか、デフォルト8000を使用
CHAINLIT_PORT=${PORT:-8000}

echo "🚀 Starting Chainlit application..."
echo "📍 Host: 0.0.0.0"
echo "🔌 Port: $CHAINLIT_PORT"
echo "🔧 Environment: Production"

# 環境変数をexport（Chainlitが認識できるように）
export CHAINLIT_HOST=0.0.0.0
export CHAINLIT_PORT=$CHAINLIT_PORT

# ヘルスチェック用の簡単なログ出力
echo "✅ Container is ready to receive requests"

# Chainlitアプリケーションを起動
exec chainlit run src/ui/app.py --host 0.0.0.0 --port "$CHAINLIT_PORT"

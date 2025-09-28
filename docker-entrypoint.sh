#!/bin/bash
set -e

# 環境変数の確認とデバッグ出力
echo "=== Environment Debug ==="
echo "Original PORT env var: ${PORT:-'not set'}"
echo "All env vars containing PORT:"
env | grep -i port || echo "No PORT variables found"

# Cloud RunのPORT環境変数を使用するか、デフォルト8000を使用
CHAINLIT_PORT=${PORT:-8000}

echo "=== Starting Chainlit Application ==="
echo "🚀 Application: Papers RAG Agent"
echo "📍 Host: 0.0.0.0"
echo "🔌 Port: $CHAINLIT_PORT"
echo "🔧 Environment: Production"

# 環境変数をexport（Chainlitが認識できるように）
export CHAINLIT_HOST=0.0.0.0
export CHAINLIT_PORT=$CHAINLIT_PORT

# 最終確認
echo "=== Final Configuration ==="
echo "CHAINLIT_HOST: $CHAINLIT_HOST"
echo "CHAINLIT_PORT: $CHAINLIT_PORT"
echo "Command: chainlit run src/ui/app.py --host 0.0.0.0 --port $CHAINLIT_PORT"

# ヘルスチェック用の簡単なログ出力
echo "✅ Container is ready to receive requests on 0.0.0.0:$CHAINLIT_PORT"

# Chainlitアプリケーションを起動（シェル形式で環境変数を確実に展開）
exec chainlit run src/ui/app.py --host 0.0.0.0 --port $CHAINLIT_PORT

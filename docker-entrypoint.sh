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
ls -la src/ui/ || echo "src/ui directory not found"

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

# uv仮想環境をアクティベート
echo "=== Activating uv virtual environment ==="
source /app/.venv/bin/activate || echo "❌ Failed to activate virtual environment"

# Python環境とモジュールの確認
echo "=== Python Environment Check ==="
python -c "import sys; print('Python executable:', sys.executable)" || echo "❌ Python import test failed"
python -c "import chainlit; print('✅ Chainlit version:', chainlit.__version__)" || echo "❌ Chainlit import failed"
python -c "import src.ui.app; print('✅ App module import successful')" || echo "❌ App module import failed"

# ヘルスチェック用の簡単なログ出力
echo "✅ Container is ready to receive requests on 0.0.0.0:$CHAINLIT_PORT"

# 最終的なポート確認
echo "=== Final Port Verification ==="
echo "Cloud Run PORT env var: ${PORT:-'not set'}"
echo "Resolved CHAINLIT_PORT: $CHAINLIT_PORT"
echo "Will bind to: 0.0.0.0:$CHAINLIT_PORT"

# Chainlit環境変数を明示的に設定（二重確認）
export CHAINLIT_HOST=0.0.0.0
export CHAINLIT_PORT=$CHAINLIT_PORT

# Chainlitアプリケーションを起動（ポート番号を明示的に指定）
echo "🚀 Starting Chainlit with command: chainlit run src/ui/app.py --host 0.0.0.0 --port $CHAINLIT_PORT"
echo "🔍 Verification: Chainlit should listen on 0.0.0.0:$CHAINLIT_PORT"

# 起動直前に最終確認
if [ -z "$CHAINLIT_PORT" ]; then
    echo "❌ FATAL: CHAINLIT_PORT is empty!"
    exit 1
fi

exec chainlit run src/ui/app.py --host 0.0.0.0 --port $CHAINLIT_PORT

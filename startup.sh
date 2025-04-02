#!/bin/bash

# デバッグモードを有効化
set -x

# エラーハンドリング関数
handle_error() {
    echo "Error occurred in script at line: ${1}"
    echo "Last command exit status: $?"
    exit 1
}

# エラーが発生した行番号をハンドリング関数に渡す
trap 'handle_error ${LINENO}' ERR

echo "=== Environment Information ==="
env | sort

echo "=== Current Directory ==="
pwd
ls -la

echo "=== Python Information ==="
which python3 || echo "Python3 not found in PATH"
python3 --version || echo "Python3 version command failed"
which pip3 || echo "Pip3 not found in PATH"
pip3 list || echo "Pip3 list command failed"

echo "=== Directory Structure ==="
echo "Contents of /home/site/wwwroot:"
ls -la /home/site/wwwroot || echo "Failed to list /home/site/wwwroot"

echo "Searching for main.py..."
MAIN_PY_PATH=$(find /home/site/wwwroot -type f -name "main.py" 2>/dev/null || echo "")
if [ -z "$MAIN_PY_PATH" ]; then
    echo "Error: Could not find main.py"
    echo "Listing all Python files:"
    find /home/site/wwwroot -type f -name "*.py" 2>/dev/null
    exit 1
fi

# アプリケーションのルートディレクトリを特定
APP_DIR=$(dirname "$MAIN_PY_PATH")
echo "Found main.py in: $APP_DIR"

echo "=== Moving to Application Directory ==="
cd "$APP_DIR" || exit 1
echo "Current directory: $(pwd)"
ls -la

echo "=== Installing Requirements ==="
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt || echo "Failed to install requirements"
fi

echo "=== Checking Required Packages ==="
pip3 list | grep -E "fastapi|uvicorn|gunicorn" || echo "Required packages not found"

# 環境変数が設定されていない場合は8000を使用
PORT=${WEBSITES_PORT:-8000}
echo "Using port: $PORT"

# PYTHONPATHにアプリケーションディレクトリを追加
export PYTHONPATH="${PYTHONPATH:+${PYTHONPATH}:}${APP_DIR}"
echo "PYTHONPATH: $PYTHONPATH"

echo "=== Testing Application Import ==="
python3 -c "import main; print('Main module can be imported')" || echo "Failed to import main module"

echo "=== Starting Application ==="
# アプリケーションを起動（詳細なログ出力）
exec gunicorn main:app \
    --bind=0.0.0.0:$PORT \
    --workers=4 \
    --worker-class=uvicorn.workers.UvicornWorker \
    --timeout=120 \
    --access-logfile=- \
    --error-logfile=- \
    --log-level=debug \
    --chdir "$APP_DIR" \
    --capture-output \
    --enable-stdio-inheritance \
    --preload 
#!/bin/bash

# 即座にエラーで終了し、未定義の変数を使用した場合にもエラーにする
set -eu

# エラーハンドリング関数
handle_error() {
    echo "Error occurred in script at line: ${1}"
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
which python || echo "Python not found in PATH"
python --version
which pip || echo "Pip not found in PATH"
pip list

echo "=== Directory Structure ==="
echo "Searching for main.py..."
MAIN_PY_PATH=$(find /home/site/wwwroot -type f -name "main.py" 2>/dev/null || echo "")
if [ -z "$MAIN_PY_PATH" ]; then
    echo "Error: Could not find main.py"
    echo "Contents of /home/site/wwwroot:"
    ls -la /home/site/wwwroot
    exit 1
fi

# アプリケーションのルートディレクトリを特定
APP_DIR=$(dirname "$MAIN_PY_PATH")
echo "Found main.py in: $APP_DIR"

echo "=== Moving to Application Directory ==="
cd "$APP_DIR"
echo "Current directory: $(pwd)"
ls -la

echo "=== Checking Requirements ==="
pip list | grep -E "fastapi|uvicorn|gunicorn" || echo "Required packages not found"

# 環境変数が設定されていない場合は8000を使用
PORT=${WEBSITES_PORT:-8000}
echo "Using port: $PORT"

# PYTHONPATHにアプリケーションディレクトリを追加
export PYTHONPATH="${PYTHONPATH:+${PYTHONPATH}:}${APP_DIR}"
echo "PYTHONPATH: $PYTHONPATH"

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
    --enable-stdio-inheritance 
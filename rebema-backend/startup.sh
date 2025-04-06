#!/bin/bash

# デバッグモードを有効化
set -x

# タイムアウト設定（秒）
DB_CHECK_TIMEOUT=30

# エラーハンドリング関数
handle_error() {
    echo "Error occurred in script at line: ${1}"
    echo "Last command exit status: $?"
    echo "Last command output:"
    echo "$(cat /tmp/last_command_output 2>/dev/null || echo 'No output available')"
    exit 1
}

# エラーが発生した行番号をハンドリング関数に渡す
trap 'handle_error ${LINENO}' ERR

# コマンド出力を一時ファイルに保存する関数
run_with_output() {
    "$@" > /tmp/last_command_output 2>&1
    cat /tmp/last_command_output
}

echo "=== Environment Information ==="
echo "Checking database environment variables..."
echo "MYSQL_HOST: ${MYSQL_HOST:-not set}"
echo "MYSQL_PORT: ${MYSQL_PORT:-not set}"
echo "MYSQL_DB: ${MYSQL_DB:-not set}"
echo "MYSQL_USER: ${MYSQL_USER:-not set}"
echo "MYSQL_SSL_MODE: ${MYSQL_SSL_MODE:-not set}"
echo "DATABASE_URL is ${DATABASE_URL:+set}${DATABASE_URL:-not set}"

echo "=== Current Directory ==="
pwd
ls -la

# クリーンアップ処理
echo "=== Cleaning up old files ==="
cd /home/site/wwwroot
if [ -f "output.tar.gz" ]; then
    echo "Removing output.tar.gz..."
    rm output.tar.gz
fi

if [ -f "oryx-manifest.toml" ]; then
    echo "Removing oryx-manifest.toml..."
    rm oryx-manifest.toml
fi

if [ -f ".ostype" ]; then
    echo "Removing .ostype..."
    rm .ostype
fi

if [ -f "hostingstart.html" ]; then
    echo "Removing hostingstart.html..."
    rm hostingstart.html
fi

echo "Current directory contents after cleanup:"
ls -la

echo "=== Python Information ==="
echo "Python Version Environment Variable: $PYTHON_VERSION"
echo "Checking all available python versions:"
run_with_output ls -la /usr/bin/python*
echo "Default Python path:"
run_with_output which python3
echo "Python version details:"
run_with_output python3 --version
run_with_output python3 -c "import sys; print(f'Python {sys.version}')"
run_with_output python3 -c "import platform; print(f'Platform Python version: {platform.python_version()}')"
echo "Pip information:"
run_with_output python3 -m pip --version
run_with_output python3 -m pip list

echo "=== Directory Structure ==="
echo "Contents of current directory:"
run_with_output ls -la

# アプリケーションのルートディレクトリを明示的に指定
APP_DIR="/home/site/wwwroot/rebema-backend"
echo "Using application directory: $APP_DIR"

echo "=== Moving to Application Directory ==="
cd "$APP_DIR" || exit 1
echo "Current directory: $(pwd)"
run_with_output ls -la

echo "=== Installing Requirements ==="
if [ -f "requirements.txt" ]; then
    echo "Installing Python packages..."
    run_with_output python3 -m pip install --user -r requirements.txt
fi

echo "=== Checking Required Packages ==="
run_with_output python3 -m pip list | grep -E "fastapi|uvicorn|gunicorn"

# 環境変数が設定されていない場合は8000を使用
PORT=${WEBSITES_PORT:-8000}
echo "Using port: $PORT"

# PYTHONPATHにアプリケーションディレクトリを追加
export PYTHONPATH="${PYTHONPATH:+${PYTHONPATH}:}$APP_DIR:$(dirname $APP_DIR)"
echo "PYTHONPATH: $PYTHONPATH"

echo "=== Testing Application Import ==="
echo "Testing main module import..."
run_with_output python3 -c "import main; print('Main module can be imported')"

echo "Testing routers import..."
run_with_output python3 -c "from routers import auth; print('Auth router can be imported')"
run_with_output python3 -c "from routers import knowledge; print('Knowledge router can be imported')"
run_with_output python3 -c "from routers import ranking; print('Ranking router can be imported')"

echo "=== Testing Database Connection ==="
echo "Running database connection test with timeout ${DB_CHECK_TIMEOUT}s..."

# タイムアウト付きでデータベース接続チェックを実行
timeout ${DB_CHECK_TIMEOUT} python3 -c "
from utils.db_check import check_database_connection
import sys
print('データベース接続チェックを開始します...')
if not check_database_connection():
    print('データベース接続テストに失敗しました')
    sys.exit(1)
print('データベース接続テストが成功しました')
" || {
    echo "Warning: Database check timed out after ${DB_CHECK_TIMEOUT}s, but continuing startup..."
}

echo "=== Starting Application ==="
echo "Starting Gunicorn with the following configuration:"
echo "- Workers: 4"
echo "- Worker Class: uvicorn.workers.UvicornWorker"
echo "- Timeout: 120s"
echo "- Port: $PORT"

exec gunicorn main:app \
    --bind=0.0.0.0:$PORT \
    --workers=4 \
    --worker-class=uvicorn.workers.UvicornWorker \
    --timeout=120 \
    --access-logfile=- \
    --error-logfile=- \
    --log-level=info \
    --chdir "$APP_DIR" \
    --capture-output \
    --enable-stdio-inheritance

STARTUP_COMMAND=bash rebema-backend/startup.sh

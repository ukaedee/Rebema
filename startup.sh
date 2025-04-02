#!/bin/bash

# デバッグ用のログ出力を有効化
set -x

# 現在のディレクトリとファイル一覧を表示
echo "Current directory: $(pwd)"
echo "Directory contents:"
ls -la

# App Serviceのデフォルトデプロイパスに移動
cd /home/site/wwwroot
echo "Changed to /home/site/wwwroot"
ls -la

# バックエンドディレクトリに移動
cd rebema-backend
echo "Changed to rebema-backend directory"
ls -la

# 環境変数が設定されていない場合は8000を使用
PORT=${WEBSITES_PORT:-8000}
echo "Using port: $PORT"

# Pythonバージョンとパスを確認
which python
python --version
which gunicorn
gunicorn --version

# gunicornでアプリケーションを起動（詳細なログ出力）
gunicorn -c gunicorn.conf.py main:app --log-level debug 
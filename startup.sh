#!/bin/bash

# 作業ディレクトリを設定
cd /home/site/wwwroot/rebema-backend

# 環境変数が設定されていない場合は8000を使用
PORT=${WEBSITES_PORT:-8000}

# gunicornでアプリケーションを起動
gunicorn -c gunicorn.conf.py main:app 
#!/bin/bash
# Docker 入口脚本 - 同时启动 API 和 Streamlit

set -e

echo "Starting DF-LCA AI Benchmark Platform..."

# 启动 API 服务（后台）
echo "Starting FastAPI service on port 8000..."
uvicorn simple_api:app --host 0.0.0.0 --port 8000 &
API_PID=$!

# 等待 API 启动
sleep 3

# 检查 API 是否启动成功
if ! kill -0 $API_PID 2>/dev/null; then
    echo "ERROR: API service failed to start"
    exit 1
fi

echo "API service started (PID: $API_PID)"

# 启动 Streamlit 服务（前台）
echo "Starting Streamlit Web UI on port 8501..."
streamlit run app.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.enableCORS false \
    --server.enableXsrfProtection false

# 如果 Streamlit 退出，也停止 API
kill $API_PID 2>/dev/null || true

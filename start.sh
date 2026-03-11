#!/bin/bash
# 启动脚本 (Linux/Mac)

echo "Starting DF-LCA AI Benchmark Platform..."
echo ""
echo "This will start:"
echo "  1. FastAPI Simple API on http://localhost:8000"
echo "  2. Streamlit Web UI on http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# 启动 API 服务（后台）
uvicorn simple_api:app --reload --host 0.0.0.0 --port 8000 &
API_PID=$!

# 等待一下让 API 启动
sleep 3

# 启动 Web 界面（前台）
echo "Starting Web UI..."
streamlit run app.py --server.port 8501 &
UI_PID=$!

# 等待用户中断
trap "echo 'Stopping services...'; kill $API_PID $UI_PID 2>/dev/null; exit" INT TERM

echo "Services started!"
echo "API: http://localhost:8000"
echo "Web UI: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop"

wait

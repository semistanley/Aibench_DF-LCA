@echo off
REM 同时启动 API 服务和 Web 界面
echo Starting DF-LCA AI Benchmark Platform...
echo.
echo This will start:
echo   1. FastAPI Simple API on http://localhost:8000
echo   2. Streamlit Web UI on http://localhost:8501
echo.
echo Press Ctrl+C to stop all services
echo.

REM 启动 API 服务（后台）
start "DF-LCA API" cmd /c "uvicorn simple_api:app --reload --host 0.0.0.0 --port 8000"

REM 等待一下让 API 启动
timeout /t 3 /nobreak >nul

REM 启动 Web 界面（前台）
echo Starting Web UI...
streamlit run app.py --server.port 8501

pause

@echo off
REM 启动 FastAPI 服务 (Full API)
echo Starting FastAPI Full API server...
echo.
echo API will be available at: http://localhost:8000
echo API docs will be available at: http://localhost:8000/docs
echo.
uvicorn api:app --reload --host 0.0.0.0 --port 8000
pause

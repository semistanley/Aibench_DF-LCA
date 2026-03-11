@echo off
REM 启动 Streamlit Web 界面
echo Starting Streamlit Web UI...
echo.
echo Web UI will be available at: http://localhost:8501
echo.
streamlit run app.py --server.port 8501
pause

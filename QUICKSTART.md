# 快速启动指南

## 方式一：使用启动脚本（推荐）

### Windows

```bash
# 同时启动 API 和 Web 界面
start_all.bat

# 或分别启动
start_api.bat          # 启动 Simple API
start_api_full.bat     # 启动 Full API
start_ui.bat            # 启动 Web 界面
```

### Linux/Mac

```bash
# 添加执行权限
chmod +x start.sh

# 同时启动 API 和 Web 界面
./start.sh
```

## 方式二：手动启动

### 1. 启动 API 服务

**Simple API（简化版）**：
```bash
uvicorn simple_api:app --reload --host 0.0.0.0 --port 8000
```

**Full API（完整版）**：
```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

### 2. 启动 Web 界面

在新的终端窗口中：
```bash
streamlit run app.py --server.port 8501
```

## 访问地址

启动成功后，可以通过以下地址访问：

- **API 服务**：http://localhost:8000
- **API 文档（Swagger）**：http://localhost:8000/docs
- **Web 界面**：http://localhost:8501

## 验证服务是否正常运行

### 检查 API 服务

```bash
# 健康检查
curl http://localhost:8000/health

# 或使用浏览器访问
# http://localhost:8000/health
```

### 检查 Web 界面

直接在浏览器中访问：http://localhost:8501

## 停止服务

- **Windows**：在运行服务的终端窗口中按 `Ctrl+C`
- **Linux/Mac**：在运行服务的终端窗口中按 `Ctrl+C`

如果使用 `start_all.bat` 或 `start.sh`，按 `Ctrl+C` 会停止所有服务。

## 常见问题

### 端口被占用

如果 8000 或 8501 端口已被占用，可以修改端口：

```bash
# 使用不同的端口
uvicorn simple_api:app --reload --port 8001
streamlit run app.py --server.port 8502
```

### 依赖未安装

如果遇到导入错误，请先安装依赖：

```bash
pip install -r requirements.txt
```

### 数据库文件

Simple API 会自动创建 `evaluations.db` 文件，无需手动创建。

## 下一步

1. ✅ 启动服务后，访问 Web 界面进行模型评测
2. ✅ 使用 API 文档（/docs）测试 API 端点
3. ✅ 查看 README.md 了解详细功能和使用方法

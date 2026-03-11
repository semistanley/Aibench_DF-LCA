# DF-LCA Benchmark Platform - 安装与配置指南

## 项目结构确认

### ✅ 核心文件（已创建）

- **`app.py`** - Streamlit Web UI 主界面
- **`api.py`** - FastAPI 后端入口（包装 `api/main.py`）
- **`evaluator.py`** - DF-LCA 评测器入口（包装 `dflca_evaluator.py`）
- **`config.yaml`** - 配置文件（应用、API、数据库、JWT 等设置）
- **`requirements.txt`** - Python 依赖列表（包含所有必需包）
- **`README.md`** - 项目文档
- **`check_setup.py`** - 安装验证脚本

### ✅ 核心目录（已创建）

- **`api/`** - FastAPI 后端（路由、认证、数据库、任务队列）
- **`core/`** - 核心模块（指标、DPU、公式、收集器）
- **`adapters/`** - 模型适配器（OpenAI、Hugging Face、Local）
- **`tasks/`** - 评测编排（引擎、评估流程）
- **`cli/`** - 命令行工具（benchmark 命令）
- **`utils/`** - 工具函数（报告生成、JSON 处理）
- **`tests/`** - 测试文件
- **`examples/`** - 使用示例
- **`docs/`** - 文档（论文提取内容）

## 依赖安装确认

### 必需的核心包

```bash
# Web 框架
streamlit==1.39.0          # Streamlit UI
fastapi==0.115.11          # FastAPI 后端
uvicorn[standard]==0.34.0  # ASGI 服务器

# 数据库
SQLAlchemy==2.0.38         # ORM
aiosqlite==0.21.0          # 异步 SQLite

# 数据处理
pandas==2.2.3              # 数据处理
matplotlib==3.9.2          # 图表绘制
plotly==5.24.1             # 交互式图表
datasets==3.0.0             # HuggingFace 数据集

# 其他工具
pydantic==2.10.6           # 数据验证
click==8.1.8               # CLI 工具
psutil==6.1.1              # 系统监控
python-jose[cryptography]==3.3.0  # JWT 认证
python-dotenv==1.0.1       # 环境变量
httpx==0.28.1              # HTTP 客户端
weasyprint==62.3           # PDF 生成
prometheus-client==0.21.0   # 监控指标
docker==7.1.0              # Docker 客户端
pyyaml==6.0.2              # YAML 解析
```

## 安装步骤

### 1. 创建虚拟环境

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 验证安装

```bash
python check_setup.py
```

应该看到：
- ✅ 所有必需的 Python 包已安装
- ✅ 所有必需的文件存在
- ✅ 所有必需的目录存在

### 4. 配置环境变量（可选）

创建 `.env` 文件：

```env
JWT_SECRET=your-secret-key-here
OPENAI_API_KEY=your-openai-api-key
HF_DATASETS_CACHE=~/.cache/huggingface/datasets
```

## 启动服务

### Streamlit Web UI

```bash
streamlit run app.py
```

访问：`http://localhost:8501`

### FastAPI 后端

```bash
# 方式1：使用 api.py
uvicorn api:app --host 0.0.0.0 --port 8000

# 方式2：使用 CLI
python -m cli.main serve --host 0.0.0.0 --port 8000
```

访问：
- API: `http://localhost:8000`
- Swagger 文档: `http://localhost:8000/docs`

## 项目文件说明

### 配置文件

- **`config.yaml`** - 主配置文件，包含：
  - 应用设置（名称、版本、调试模式）
  - API 设置（主机、端口、工作进程）
  - Streamlit 设置（主机、端口、主题）
  - 数据库设置（URL、连接池）
  - JWT 认证设置
  - 模型注册表设置
  - 评测设置（默认能耗方法、采样间隔）
  - 监控设置（Prometheus）
  - 日志设置
  - 报告生成设置
  - 任务设置

### 入口文件

- **`app.py`** - Streamlit 应用主入口
- **`api.py`** - FastAPI 应用入口（简化包装）
- **`evaluator.py`** - DF-LCA 评测器入口（简化包装）

### 核心模块

- **`dflca_evaluator.py`** - DF-LCA 核心评测器（5 个维度）
- **`models.py`** - 模型注册中心
- **`benchmark_tasks.py`** - 标准评测任务管理
- **`reporter.py`** - 报告生成器（HTML/PDF）

## 验证清单

运行 `python check_setup.py` 后，应该看到：

```
[SUCCESS] All required packages are installed!
[SUCCESS] All required files are present!
[SUCCESS] All required directories are present!
[SUCCESS] Setup is complete! All requirements are met.
```

如果有缺失的包，脚本会提示安装：

```bash
pip install -r requirements.txt
```

## 下一步

1. ✅ 安装所有依赖：`pip install -r requirements.txt`
2. ✅ 运行验证脚本：`python check_setup.py`
3. ✅ 启动 Streamlit UI：`streamlit run app.py`
4. ✅ 启动 FastAPI 后端：`uvicorn api:app --reload`
5. ✅ 开始评测：使用 UI 或 CLI 进行模型评测

## 故障排除

### 问题：某些包安装失败

**解决方案**：
- 确保 Python 版本 >= 3.10
- 使用 `pip install --upgrade pip` 升级 pip
- 对于 Windows，某些包可能需要 Visual C++ 编译器

### 问题：PDF 生成失败

**解决方案**：
- WeasyPrint 需要系统依赖（Cairo、Pango 等）
- Windows: 可能需要安装 GTK+ 运行时
- Linux: `sudo apt-get install python3-cffi python3-brotli libpango-1.0-0 libpangoft2-1.0-0`
- Mac: `brew install cairo pango gdk-pixbuf libffi`

### 问题：数据集加载失败

**解决方案**：
- 确保安装了 `datasets` 库
- 检查网络连接（HuggingFace 数据集需要下载）
- 设置缓存目录：`export HF_DATASETS_CACHE=~/.cache/huggingface/datasets`

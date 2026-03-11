# AI Bench DF-LCA Platform

DF-LCA（Digital Footprint - Life Cycle Assessment）框架下的 AI 评测平台项目骨架：

- **Performance**：延迟、吞吐、token 计数（占位估算）
- **Energy**：能耗（占位估算，后续可接入真实计量）
- **Value**：质量/成本/碳排（接口已留好，当前占位）

## 目录结构

- `core/`: 指标与核心数据结构（DF-LCA 三维）
- `adapters/`: 模型适配器（OpenAI / Hugging Face / Local）
- `tasks/`: 评测编排（一次评测的端到端流程）
- `api/`: FastAPI REST API + SQLite 持久化
- `cli/`: 命令行入口
- `app.py`: Streamlit Web UI（模型选择、任务配置、结果可视化）
- `dflca_evaluator.py`: DF-LCA 核心评测器（封装 5 个核心评测维度）
- `models.py`: 模型注册中心（统一管理模型配置）
- `benchmark_tasks.py`: 标准评测任务和数据集管理（MMLU, BBH, GSM8K, HumanEval, MBPP 等）

## API 选择

项目提供两种 FastAPI 后端：

### 1. Simple API（简化版）

`simple_api.py` - 使用 `SimpleEvaluator` 和 SQLite，适合快速原型和简单评测：

```bash
# 启动 Simple API
uvicorn simple_api:app --host 0.0.0.0 --port 8000
```

**特性**：
- ✅ 使用 `SimpleEvaluator` 进行快速评测
- ✅ SQLite 数据库存储（`evaluations.db`）
- ✅ 简单的 REST API 端点
- ✅ 无需 JWT 认证（适合开发测试）

**端点**：
- `POST /evaluate` - 执行模型评测
- `GET /results` - 获取所有评测结果
- `GET /results/{model_name}` - 获取指定模型的历史
- `GET /models` - 列出所有已评测的模型
- `GET /health` - 健康检查

### 2. Full API（完整版）

`api/main.py` - 完整的 DF-LCA 平台 API，包含异步 SQLAlchemy、JWT 认证等：

```bash
# 启动 Full API
uvicorn api:app --host 0.0.0.0 --port 8000
```

**特性**：
- ✅ 完整的 DF-LCA 评测（5 个核心维度）
- ✅ 异步 SQLAlchemy + SQLite
- ✅ JWT 认证
- ✅ 任务队列支持
- ✅ 标准化报告生成

## 🚀 快速启动

### Docker 部署（推荐用于生产环境）

```bash
# 使用 docker-compose（最简单）
docker-compose up -d

# 或手动构建和运行
docker build -t dflca-benchmark .
docker run -d -p 8000:8000 -p 8501:8501 dflca-benchmark
```

详细说明请查看 [DOCKER.md](DOCKER.md)

### 本地启动（开发环境）

#### 一键启动（推荐）

**Windows**：
```bash
# 同时启动 API 和 Web 界面
start_all.bat

# 或分别启动
start_api.bat          # 启动 Simple API
start_api_full.bat     # 启动 Full API  
start_ui.bat            # 启动 Web 界面
```

**Linux/Mac**：
```bash
chmod +x start.sh
./start.sh
```

### 手动启动

**启动 API 服务**：
```bash
# Simple API（简化版）
uvicorn simple_api:app --reload --host 0.0.0.0 --port 8000

# Full API（完整版）
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

**启动 Web 界面**（新终端）：
```bash
streamlit run app.py --server.port 8501
```

### 访问地址

- **API 服务**：http://localhost:8000
- **API 文档**：http://localhost:8000/docs
- **Web 界面**：http://localhost:8501

详细说明请查看 [QUICKSTART.md](QUICKSTART.md)

## 快速开始

### 1. 创建项目结构

项目已经创建完成，包含以下核心文件：

- `app.py` - Streamlit 主界面
- `api.py` - FastAPI 后端入口（包装 `api/main.py`）
- `evaluator.py` - DF-LCA 评测器入口（包装 `dflca_evaluator.py`）
- `config.yaml` - 配置文件
- `requirements.txt` - Python 依赖列表

### 2. 创建虚拟环境并安装依赖

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate

# 安装所有依赖
pip install -r requirements.txt
```

### 3. 验证安装

运行安装验证脚本：

```bash
python check_setup.py
```

这将检查：
- ✅ 所有必需的 Python 包是否已安装
- ✅ 所有必需的文件是否存在
- ✅ 所有必需的目录是否存在

### 4. 配置环境变量（可选）

创建 `.env` 文件（可选）：

```bash
JWT_SECRET=your-secret-key-here
OPENAI_API_KEY=your-openai-api-key
HF_DATASETS_CACHE=~/.cache/huggingface/datasets
```

启动服务：

```bash
python -m cli.main serve --host 127.0.0.1 --port 8000
```

或启动 Streamlit Web UI：

```bash
streamlit run app.py
```

访问 `http://localhost:8501` 使用可视化界面进行模型评测。

### Simple API 使用示例

```bash
# 启动 Simple API
uvicorn simple_api:app --host 0.0.0.0 --port 8000

# 执行评测
curl -X POST http://127.0.0.1:8000/evaluate ^
  -H "Content-Type: application/json" ^
  -d "{\"model_name\":\"GPT-4\",\"tasks\":[\"MMLU\",\"GSM8K\"],\"model_endpoint\":\"http://api.example.com/v1/completions\"}"

# 获取结果
curl http://127.0.0.1:8000/results/GPT-4
```

### Full API 使用示例

调用评测接口（示例使用本地 Local Echo 适配器）：

```bash
curl -X POST http://127.0.0.1:8000/v1/evaluate ^
  -H "Content-Type: application/json" ^
  -d "{\"task_name\":\"demo\",\"input\":{\"prompt\":\"hello\"},\"model\":{\"provider\":\"local\",\"model\":\"echo\"}}"
```

查看结果：

- Swagger: `http://127.0.0.1:8000/docs`

## JWT 认证（Bearer Token）

受保护端点（例如 `/evaluate`、`/results/{id}`、`/leaderboard`）需要：

- Header：`Authorization: Bearer <token>`
- 服务端密钥：环境变量 `JWT_SECRET`（未设置时会使用开发默认值，不建议用于生产）

生成一个测试 token（示例）：

```bash
set JWT_SECRET=dev-only-secret
python -c "from api.auth import create_access_token; print(create_access_token({'sub':'demo'}))"
```

## DF-LCA 方法论对齐（论文）

本项目的骨架实现参考了 DF-LCA 的关键定义：

- **Processing unit**：用 DPU（Data Processing Unit）抽象数据处理单元
- **Functional unit**：用 **unit data**（单位数据）做指标标准化（例如每 KB 的延迟/能耗）

论文（Part 1）：

- Qiang Huang, *How to assess the digitization and digital effort: A framework for Digitization Footprint (Part 1)*, Computers and Electronics in Agriculture, 230 (2025) 109875. DOI: `10.1016/j.compag.2024.109875`

论文（Part 2，指标与计算方法）：

- Qiang Huang, *Indicators to Digitization Footprint and How to Get Digitization Footprint (Part 2)*, Computers and Electronics in Agriculture, 224 (2024) 109206. DOI: `10.1016/j.compag.2024.109206`

## 能耗采集策略（可选项）

评测请求支持通过 `options.energy_method` 选择能耗/功耗采集方式，并会写入每次 run 的 artifacts 用于可追溯：

- `cpu_estimate`：默认，基于 CPU 利用率的功耗估算（可跑通但精度有限）
- `external_meter`：外部电表接口（当前为 stub，占位；后续可接串口/网络电表）
- `sensors`：GPU/CPU 传感器库接口（当前为 stub，占位；后续可接 NVML / RAPL 等）

示例（选择外部电表模式）：

```bash
curl -X POST http://127.0.0.1:8000/v1/evaluate ^
  -H "Content-Type: application/json" ^
  -d "{\"task_name\":\"demo\",\"input\":{\"prompt\":\"hello\"},\"model\":{\"provider\":\"local\",\"model\":\"echo\"},\"options\":{\"energy_method\":\"external_meter\",\"sample_interval_s\":0.25}}"
```

## 评测器选择

项目提供两种评测器：

### 1. SimpleEvaluator（简化版）

`simple_evaluator.py` 提供了快速评测功能，适合快速测试和原型开发：

```python
from evaluator import SimpleEvaluator

# 创建评测器
evaluator = SimpleEvaluator()

# 执行评测
metrics = evaluator.evaluate_model(
    model_endpoint="http://api.example.com/v1/completions",
    tasks=["MMLU", "GSM8K"]
)

# 查看结果
print(f"准确率: {metrics['performance']['accuracy']:.2%}")
print(f"延迟: {metrics['performance']['latency_ms']:.2f} ms")
print(f"CPU使用率: {metrics['efficiency']['cpu_usage']:.2f}%")
print(f"碳排放: {metrics['carbon']['carbon_footprint_g']:.4f} gCO2e")
```

**特性**：
- ✅ 快速评测（性能、能效、碳排放）
- ✅ 支持 MMLU、GSM8K、BBH、HumanEval 等任务
- ✅ 自动收集 CPU、内存使用率
- ✅ 基于能耗的碳排放估算

### 2. DFLCAEvaluator（完整版）

`dflca_evaluator.py` 提供了封装好的 DF-LCA 核心评测器，包含 5 个核心评测维度：

1. **Task Performance（任务性能）**：延迟、吞吐量、token 计数
2. **Computational Efficiency（计算效率）**：MIPS/FLOPs  per byte、数据生成速度
3. **Energy Consumption（能耗分析）**：总能耗、单位数据能耗
4. **Resource Utilization（资源利用率）**：CPU/内存利用率、峰值使用
5. **Carbon Footprint（碳排放估算）**：碳排放量（gCO2e）、单位数据碳排放

使用示例：

```python
import asyncio
from dflca_evaluator import DFLCAEvaluator
from core.schemas import ModelConfig, ModelProvider

# 创建评测器
evaluator = DFLCAEvaluator()

# 配置模型
model = ModelConfig(provider=ModelProvider.local, model="echo")

# 定义任务
tasks = [{"prompt": "Hello, world!"}]

# 执行评测
result = asyncio.run(evaluator.evaluate(model, tasks))

# 查看结果
print("Performance:", result["performance"])
print("Efficiency:", result["efficiency"])
print("Energy:", result["energy"])
print("Carbon:", result["carbon"])
print("Resource:", result["resource"])
```

也支持同步调用：

```python
from dflca_evaluator import evaluate

result = evaluate(model, tasks)
```

## 标准评测任务（BenchmarkTasks）

`benchmark_tasks.py` 提供了标准评测数据集的管理和加载功能：

### 支持的任务类别

- **reasoning**：MMLU, BBH, GSM8K
- **coding**：HumanEval, MBPP
- **knowledge**：TriviaQA, Natural Questions
- **openclaw_specific**：Tool usage, API calling, Workflow execution

### 使用示例

```python
from benchmark_tasks import BenchmarkTasks
from core.schemas import ModelConfig, ModelProvider

# 创建任务管理器
tasks = BenchmarkTasks()

# 列出所有任务
print("Available tasks:", tasks.list_tasks())

# 加载数据集
gsm8k_samples = tasks.load_dataset("gsm8k", limit=10)
print(f"Loaded {len(gsm8k_samples)} GSM8K samples")

# 获取任务信息
info = tasks.get_task_info("mmlu")
print("MMLU info:", info)

# 创建评测请求
model = ModelConfig(provider=ModelProvider.local, model="echo")
requests = tasks.create_evaluation_request("gsm8k", model, limit=5)
print(f"Created {len(requests)} evaluation requests")
```

### 数据集依赖

标准评测数据集需要安装 `datasets` 库：

```bash
pip install datasets
```

本地自定义任务（如 `tool_usage`, `api_calling`）需要提供 JSON 格式的数据文件。

## 报告生成器（ReportGenerator）

`reporter.py` 提供了完整的 HTML/PDF 报告生成功能，包含：

1. **综合评分（Overall Score）**：基于性能、能耗、碳排放、价值和资源利用率的综合评分（0-100分）
2. **性能对比图表（Performance Comparison Charts）**：使用 Plotly 生成交互式图表
3. **能效分析（Energy Efficiency Analysis）**：详细的能耗和碳排放分析
4. **改进建议（Improvement Recommendations）**：基于评测结果自动生成的优化建议

### 使用示例

```python
from reporter import ReportGenerator, generate_report
from core.schemas import EvaluationResult

# 方式1：使用类
generator = ReportGenerator()
report_path = generator.generate_report(
    evaluation_results,
    format="html",  # 或 "pdf"
    output_path="report.html",
    include_charts=True,
    compare_models=False,
)

# 方式2：使用便捷函数
report_path = generate_report(evaluation_results, format="html")

# 多模型对比
results = [result1, result2, result3]
report_path = generator.generate_report(
    results,
    format="html",
    compare_models=True,  # 生成对比图表
)
```

### 报告内容

生成的报告包含以下部分：

- **Summary（摘要）**：Run ID、任务、模型、创建时间、总体评分
- **Overall Score Breakdown（综合评分分解）**：各维度得分详情
- **Performance & Energy Charts（性能与能耗图表）**：交互式可视化
- **Performance Metrics（性能指标）**：延迟、吞吐量、准确率等
- **Energy Metrics（能耗指标）**：总能耗、功率、碳排放等
- **Energy Efficiency Analysis（能效分析）**：单位数据能耗、DF-LCA Part 2 指标
- **Improvement Recommendations（改进建议）**：基于评测结果的优化建议
- **Detailed Information（详细信息）**：输入/输出、标签等完整信息

### PDF 生成依赖

PDF 报告生成需要安装 `weasyprint`：

```bash
pip install weasyprint
```

注意：PDF 生成在某些系统上可能需要额外的系统依赖（如 Cairo、Pango 等）。

### 报告模板

平台支持多种报告模板，满足不同需求：

- **Academic（学术）**：适合论文发表，包含详细的实验方法和引用格式
- **Engineering（工程）**：技术团队使用，关注性能指标和优化建议
- **Executive（管理层）**：商业决策使用，突出关键指标和商业价值
- **Sustainability（可持续性）**：环保评估使用，侧重碳排放和环境指标

使用示例：

```python
from reporter import ReportGenerator

# 生成学术报告
generator = ReportGenerator(template="academic")
report_path = generator.generate_report(
    evaluation_result,
    format="html",
    template="academic"
)
```

API 使用：

```bash
# 获取可用模板
GET /templates

# 生成报告（指定模板）
GET /results/{evaluation_id}/report?template=academic&format=html
```

详细说明请查看 [REPORT_TEMPLATES.md](REPORT_TEMPLATES.md)

## 测试

### 快速测试

使用简单测试脚本快速测试 API：

```bash
# 确保 API 服务正在运行
uvicorn simple_api:app --host 0.0.0.0 --port 8000

# 在另一个终端运行测试
python test_evaluation_simple.py
```

### 完整测试套件

运行完整的测试套件，包含多个测试用例：

```bash
python test_evaluation.py
```

测试套件包括：
- ✅ 健康检查
- ✅ 评测API
- ✅ 获取评测结果
- ✅ 获取所有结果
- ✅ 列出所有模型
- ✅ 错误处理（无效请求）
- ✅ 边界情况（不存在的模型）

### 测试配置

在运行测试前，请确保：

1. **API 服务已启动**：
   ```bash
   uvicorn simple_api:app --host 0.0.0.0 --port 8000
   ```

2. **模型端点可用**（可选）：
   - 如果使用真实的模型端点，确保端点可访问
   - 如果端点不可用，测试会使用模拟响应

3. **依赖已安装**：
   ```bash
   pip install requests
   ```

## Badge 徽章系统

平台提供徽章生成功能，可以在 GitHub README 中展示评测结果。

### 快速使用

```markdown
![DF-LCA Benchmark](https://benchmark.dflca.ai/badge/model/my-awesome-model.svg)
![Score](https://benchmark.dflca.ai/badge/score/85/blue.svg)
![Efficiency](https://benchmark.dflca.ai/badge/efficiency/A+/green.svg)
```

### 支持的徽章类型

- **分数徽章**：`/badge/score/{score}`
- **能效等级**：`/badge/efficiency/{grade}`
- **性能（延迟）**：`/badge/performance/{latency_ms}`
- **碳排放**：`/badge/carbon/{carbon_gco2e}`
- **模型评测**：`/badge/model/{model_name}`
- **自定义徽章**：`/badge/custom?label=...&message=...`

详细说明请查看 [BADGES.md](BADGES.md)

## 排行榜系统

评测结果可以自动发布到全球公开排行榜。

### 自动发布

执行评测时，结果会自动发布到排行榜（默认启用）：

```bash
curl -X POST "http://localhost:8000/evaluate?publish_to_leaderboard=true" \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "my-model",
    "tasks": ["MMLU", "GSM8K"],
    "model_endpoint": "http://api.example.com/v1/completions"
  }'
```

响应中包含排行榜信息：

```json
{
  "leaderboard": {
    "leaderboard_url": "https://benchmark.dflca.ai/leaderboard",
    "model_url": "https://benchmark.dflca.ai/models/my-model",
    "rank": 42,
    "total_entries": 100,
    "percentile": 85.0
  }
}
```

### 获取排行榜

```bash
# 获取全部排行榜
GET /leaderboard

# 按任务筛选
GET /leaderboard?task_name=MMLU

# 获取模型统计
GET /leaderboard/models/{model_name}
```

详细说明请查看 [LEADERBOARD.md](LEADERBOARD.md)
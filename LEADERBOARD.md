# 排行榜系统

DF-LCA AI Benchmark 平台提供自动排行榜功能，评测结果可以自动发布到全球公开排行榜。

## 功能特性

- ✅ **自动发布**：评测完成后自动发布到排行榜
- ✅ **排名计算**：自动计算排名和百分位数
- ✅ **多维度排序**：支持按综合得分、性能、能效等排序
- ✅ **任务分类**：支持按任务类型筛选
- ✅ **模型统计**：提供详细的模型统计信息
- ✅ **公开/私有**：支持公开和私有模式

## 快速开始

### 自动发布（默认）

执行评测时，结果会自动发布到排行榜：

```bash
curl -X POST "http://localhost:8000/evaluate?publish_to_leaderboard=true" \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "my-awesome-model",
    "tasks": ["MMLU", "GSM8K"],
    "model_endpoint": "http://api.example.com/v1/completions"
  }'
```

响应中会包含排行榜信息：

```json
{
  "status": "success",
  "model": "my-awesome-model",
  "metrics": {...},
  "evaluation_id": 123,
  "leaderboard": {
    "leaderboard_url": "https://benchmark.dflca.ai/leaderboard",
    "model_url": "https://benchmark.dflca.ai/models/my-awesome-model",
    "rank": 42,
    "total_entries": 100,
    "percentile": 85.0,
    "is_public": true
  }
}
```

### 禁用自动发布

如果不想自动发布，可以设置 `publish_to_leaderboard=false`：

```bash
curl -X POST "http://localhost:8000/evaluate?publish_to_leaderboard=false" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

### 手动发布

也可以手动发布已有的评测结果：

```bash
curl -X POST "http://localhost:8000/leaderboard/publish?evaluation_id=123&make_public=true"
```

## API 端点

### 获取排行榜

```bash
# 获取全部排行榜
GET /leaderboard

# 按任务筛选
GET /leaderboard?task_name=MMLU

# 限制返回数量
GET /leaderboard?limit=50

# 包含私有记录（需要权限）
GET /leaderboard?include_private=true
```

响应示例：

```json
{
  "task_name": null,
  "total": 100,
  "entries": [
    {
      "rank": 1,
      "model_name": "best-model",
      "score": 95.5,
      "performance_score": 90.0,
      "efficiency_score": 95.0,
      "carbon_score": 100.0,
      "latency_ms": 50.0,
      "energy_joules": 0.001,
      "carbon_gco2e": 0.0001,
      "accuracy": 0.95,
      "submitted_at": "2024-01-01 12:00:00"
    },
    ...
  ]
}
```

### 获取模型统计信息

```bash
GET /leaderboard/models/{model_name}
```

响应示例：

```json
{
  "model_name": "my-awesome-model",
  "total_submissions": 10,
  "avg_score": 85.5,
  "best_score": 92.0,
  "worst_score": 78.0,
  "tasks_count": 3
}
```

## 排行榜页面

访问排行榜页面查看所有公开结果：

- **全局排行榜**：https://benchmark.dflca.ai/leaderboard
- **模型详情**：https://benchmark.dflca.ai/models/{model_name}

## 排名计算

### 综合得分

综合得分（0-100）基于以下维度：

- **性能得分**（0-40分）
  - 准确率：0-40分
  - 延迟：0-20分（<100ms=20分，<500ms=15分，<1000ms=10分，≥1000ms=5分）

- **能效得分**（0-30分）
  - CPU使用率：<30%=30分，<50%=25分，<70%=20分，≥70%=10分

- **碳排放得分**（0-30分）
  - <0.001g=30分，<0.01g=25分，<0.1g=20分，≥0.1g=10分

### 排名和百分位数

- **排名**：按综合得分降序排列，得分相同按提交时间排序
- **百分位数**：表示超过多少百分比的模型

## 使用示例

### Python 示例

```python
import requests

# 执行评测并自动发布
response = requests.post(
    "http://localhost:8000/evaluate",
    params={"publish_to_leaderboard": True},
    json={
        "model_name": "my-model",
        "tasks": ["MMLU"],
        "model_endpoint": "http://api.example.com/v1/completions"
    }
)

result = response.json()
if result.get("leaderboard"):
    print(f"排名: {result['leaderboard']['rank']}")
    print(f"百分位数: {result['leaderboard']['percentile']}%")
    print(f"排行榜URL: {result['leaderboard']['leaderboard_url']}")

# 获取排行榜
leaderboard = requests.get("http://localhost:8000/leaderboard").json()
for entry in leaderboard["entries"][:10]:
    print(f"{entry['rank']}. {entry['model_name']}: {entry['score']:.2f}")
```

### 集成到 CI/CD

```yaml
# GitHub Actions 示例
name: Benchmark and Publish

on:
  push:
    branches: [main]

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Evaluation
        run: |
          curl -X POST "${{ secrets.BENCHMARK_API }}/evaluate?publish_to_leaderboard=true" \
            -H "Content-Type: application/json" \
            -d '{
              "model_name": "${{ github.repository }}",
              "tasks": ["MMLU", "GSM8K"],
              "model_endpoint": "${{ secrets.MODEL_ENDPOINT }}"
            }'
      
      - name: Update README
        run: |
          # 获取排名并更新 README
          RANK=$(curl -s "${{ secrets.BENCHMARK_API }}/leaderboard/models/${{ github.repository }}" | jq '.rank')
          echo "Rank: $RANK" >> README.md
```

## 数据隐私

- **公开模式**：结果会出现在公开排行榜中
- **私有模式**：结果仅存储，不公开显示
- **数据安全**：所有数据存储在本地 SQLite 数据库中

## 故障排除

### 排行榜未更新

1. 检查 `publish_to_leaderboard` 参数是否为 `true`
2. 确认评测是否成功完成
3. 查看 API 响应中的 `leaderboard` 字段

### 排名不正确

1. 确认任务名称一致（相同任务才会一起排名）
2. 检查综合得分计算是否正确
3. 查看数据库中的记录

### 模型未出现在排行榜

1. 确认 `is_public` 为 `true`
2. 检查是否有相同任务的记录
3. 查看模型统计信息确认提交是否成功

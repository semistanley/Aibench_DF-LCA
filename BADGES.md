# Badge 徽章系统

DF-LCA AI Benchmark 平台提供徽章生成功能，可以在 GitHub README 或其他文档中展示评测结果。

## 快速开始

### 基本用法

在 GitHub README 中添加徽章：

```markdown
![DF-LCA Benchmark](https://benchmark.dflca.ai/badge/model/my-awesome-model.svg)
```

### 支持的徽章类型

#### 1. 分数徽章

```markdown
![Score](https://benchmark.dflca.ai/badge/score/85/blue.svg)
```

参数：
- `score`: 分数（0-100）
- `color`: 可选的颜色（blue, green, yellow, orange, red等）

颜色会根据分数自动选择：
- ≥80: brightgreen
- ≥60: green
- ≥40: yellowgreen
- ≥20: yellow
- <20: red

#### 2. 能效等级徽章

```markdown
![Efficiency](https://benchmark.dflca.ai/badge/efficiency/A+/green.svg)
```

参数：
- `grade`: 等级（A+, A, B, C, D, F）
- `color`: 可选的颜色

#### 3. 性能徽章（延迟）

```markdown
![Latency](https://benchmark.dflca.ai/badge/performance/150/blue.svg)
```

参数：
- `latency_ms`: 延迟（毫秒）
- `color`: 可选的颜色

#### 4. 碳排放徽章

```markdown
![Carbon](https://benchmark.dflca.ai/badge/carbon/0.001/green.svg)
```

参数：
- `carbon_gco2e`: 碳排放量（gCO2e）
- `color`: 可选的颜色

#### 5. 模型评测徽章

```markdown
![DF-LCA Benchmark](https://benchmark.dflca.ai/badge/model/my-awesome-model.svg)
```

参数：
- `model_name`: 模型名称
- `score`: 可选的综合得分（查询参数）

#### 6. 自定义徽章

```markdown
![Custom](https://benchmark.dflca.ai/badge/custom?label=MyLabel&message=MyMessage&color=blue)
```

参数：
- `label`: 左侧标签
- `message`: 右侧消息
- `color`: 颜色
- `style`: 样式（flat, plastic, flat-square）

## API 端点

### 本地部署

如果使用本地部署的 API，将 URL 替换为：

```
http://localhost:8000/badge/...
```

### 端点列表

- `GET /badge/score/{score}` - 分数徽章
- `GET /badge/efficiency/{grade}` - 能效等级徽章
- `GET /performance/{latency_ms}` - 性能徽章
- `GET /badge/carbon/{carbon_gco2e}` - 碳排放徽章
- `GET /badge/model/{model_name}` - 模型评测徽章
- `GET /badge/custom` - 自定义徽章
- `GET /badge/result/{evaluation_id}` - 根据评测结果生成所有徽章

## 使用示例

### 在 README 中展示评测结果

```markdown
# My Awesome Model

![DF-LCA Score](https://benchmark.dflca.ai/badge/score/85/brightgreen.svg)
![Efficiency](https://benchmark.dflca.ai/badge/efficiency/A+/green.svg)
![Latency](https://benchmark.dflca.ai/badge/performance/150/blue.svg)
![Carbon](https://benchmark.dflca.ai/badge/carbon/0.001/green.svg)
```

### 根据评测结果自动生成

访问 `/badge/result/{evaluation_id}` 可以查看所有徽章的预览和 Markdown 代码。

## 颜色选项

支持的颜色：
- `blue` - 蓝色（默认）
- `green` / `brightgreen` - 绿色
- `yellow` / `yellowgreen` - 黄色
- `orange` - 橙色
- `red` - 红色
- `lightgrey` - 浅灰色

## 样式选项

支持的样式（仅自定义徽章）：
- `flat` - 扁平样式（默认）
- `plastic` - 塑料样式
- `flat-square` - 扁平方形

## 集成到 CI/CD

### GitHub Actions 示例

```yaml
name: Update Badges

on:
  workflow_run:
    workflows: ["Evaluation"]
    types:
      - completed

jobs:
  update-badges:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Update README badges
        run: |
          # 获取评测结果
          SCORE=$(curl -s https://benchmark.dflca.ai/api/results/my-model | jq '.latest.score')
          
          # 更新 README
          sed -i "s|badge/score/[0-9]*|badge/score/$SCORE|g" README.md
```

## 注意事项

1. **URL 编码**：模型名称等参数会自动进行 URL 编码
2. **缓存**：浏览器可能会缓存徽章，更新可能需要清除缓存
3. **HTTPS**：生产环境建议使用 HTTPS
4. **自定义域名**：可以配置自定义域名替代 `benchmark.dflca.ai`

## 故障排除

### 徽章不显示

1. 检查 URL 是否正确
2. 确认 API 服务正在运行
3. 检查网络连接

### 颜色不正确

1. 确认颜色参数拼写正确
2. 某些徽章类型会根据值自动选择颜色

### 样式问题

1. 确认样式参数支持（仅自定义徽章）
2. 某些浏览器可能对 SVG 渲染有差异

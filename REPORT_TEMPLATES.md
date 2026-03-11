# 报告模板系统

DF-LCA AI Benchmark 平台支持多种报告模板，满足不同用户群体的需求。

## 可用模板

### 1. Academic（学术模板）

**适合场景**：论文发表、学术研究、技术文档

**特点**：
- 详细的实验方法说明
- 完整的统计数据展示
- 符合学术规范的引用格式
- 详细的图表说明
- DF-LCA Part 2 标准化指标表格

**使用示例**：

```python
from reporter import ReportGenerator

generator = ReportGenerator(template="academic")
report_path = generator.generate_report(
    evaluation_result,
    format="html",
    output_path="academic_report.html"
)
```

### 2. Engineering（工程模板）

**适合场景**：技术团队、系统优化、性能分析

**特点**：
- 技术指标详细展示
- 性能对比图表
- 系统架构信息
- 优化建议
- 完整的指标分解

**使用示例**：

```python
generator = ReportGenerator(template="engineering")
report_path = generator.generate_report(evaluation_result)
```

### 3. Executive（管理层模板）

**适合场景**：商业决策、投资评估、管理层汇报

**特点**：
- 关键指标摘要（大数字展示）
- 商业价值分析
- 成本效益分析
- 决策建议
- 简洁明了的可视化

**使用示例**：

```python
generator = ReportGenerator(template="executive")
report_path = generator.generate_report(
    evaluation_result,
    format="pdf"  # 适合打印和分享
)
```

### 4. Sustainability（可持续性模板）

**适合场景**：环保评估、ESG 报告、可持续性分析

**特点**：
- 碳排放详细分析
- 环境影响评估
- 可持续性指标
- 绿色计算建议
- 碳足迹可视化

**使用示例**：

```python
generator = ReportGenerator(template="sustainability")
report_path = generator.generate_report(evaluation_result)
```

## API 使用

### 获取可用模板列表

```bash
GET /templates
```

响应：

```json
{
  "templates": {
    "academic": {
      "name": "Academic",
      "description": "适合论文发表的格式",
      "features": ["详细的实验方法", "完整的统计数据", "引用格式", "图表说明"]
    },
    ...
  },
  "default": "engineering"
}
```

### 生成报告

```bash
GET /results/{evaluation_id}/report?template=academic&format=html
```

参数：
- `template`: 模板名称（academic, engineering, executive, sustainability）
- `format`: 输出格式（html 或 pdf）

### Python 使用示例

```python
from reporter import ReportGenerator, REPORT_TEMPLATES

# 查看所有可用模板
print("Available templates:")
for name, config in REPORT_TEMPLATES.items():
    print(f"  {name}: {config['description']}")

# 生成学术报告
generator = ReportGenerator(template="academic")
report_path = generator.generate_report(
    evaluation_result,
    format="html",
    include_charts=True,
)
```

## 模板对比

| 特性 | Academic | Engineering | Executive | Sustainability |
|------|----------|-------------|-----------|----------------|
| 详细程度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| 技术深度 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| 商业视角 | ⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| 环保重点 | ⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ |
| 适合打印 | ✅ | ✅ | ✅✅ | ✅ |

## 自定义模板

可以通过继承 `ReportGenerator` 类来创建自定义模板：

```python
from reporter import ReportGenerator

class CustomReportGenerator(ReportGenerator):
    def _generate_custom_content(self, results, scores, charts_html, recommendations, single_result):
        # 实现自定义内容生成逻辑
        return "<section>Custom content</section>"
    
    def _generate_html(self, results, single_result, include_charts, compare_models, template="custom"):
        # 调用自定义内容生成
        content = self._generate_custom_content(...)
        # 构建 HTML
        return html
```

## 最佳实践

1. **论文发表**：使用 `academic` 模板，导出为 PDF
2. **技术文档**：使用 `engineering` 模板，HTML 格式便于在线查看
3. **商业汇报**：使用 `executive` 模板，PDF 格式便于打印和分享
4. **ESG 报告**：使用 `sustainability` 模板，突出环保指标

## 模板样式

每个模板都有独特的视觉风格：

- **Academic**：学术风格，使用 Times New Roman 字体，深蓝色主题
- **Engineering**：技术风格，绿色主题，强调数据和图表
- **Executive**：商务风格，蓝色主题，大数字展示，简洁明了
- **Sustainability**：环保风格，绿色主题，突出碳排放和环境指标

## 故障排除

### 模板不存在

如果指定的模板不存在，会使用默认的 `engineering` 模板。

### PDF 生成失败

PDF 生成需要 `weasyprint` 库，某些系统可能需要额外的系统依赖。建议先使用 HTML 格式测试。

### 样式显示异常

确保浏览器支持现代 CSS 特性。某些旧版浏览器可能无法正确显示所有样式。

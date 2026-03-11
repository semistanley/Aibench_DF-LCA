"""FastAPI后端 - 简化版，使用 SimpleEvaluator 和 SQLite"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

from simple_evaluator import SimpleEvaluator
from utils.badge import (
    generate_badge,
    generate_score_badge,
    generate_efficiency_badge,
    generate_performance_badge,
    generate_carbon_badge,
    generate_model_badge,
)
from utils.leaderboard import Leaderboard
from reporter import ReportGenerator, REPORT_TEMPLATES
from core.schemas import EvaluationResult

app = FastAPI(
    title="DF-LCA AI Benchmark API (Simple)",
    description="简化版评测API，使用 SimpleEvaluator 和 SQLite",
    version="1.0.0",
)

# 初始化评测器
evaluator = SimpleEvaluator()

# 初始化排行榜
leaderboard = Leaderboard()

# 数据库文件路径
DB_PATH = Path("evaluations.db")


class EvaluationRequest(BaseModel):
    """评测请求模型"""
    model_name: str = Field(..., description="模型名称")
    tasks: List[str] = Field(..., description="评测任务列表，如 ['MMLU', 'GSM8K']")
    model_endpoint: str = Field(..., description="模型API端点URL")


class EvaluationResponse(BaseModel):
    """评测响应模型"""
    status: str
    model: str
    metrics: dict
    evaluation_id: Optional[int] = None
    leaderboard: Optional[dict] = None


class ResultItem(BaseModel):
    """结果项模型"""
    id: int
    model_name: str
    timestamp: str
    metrics: dict


class ResultsResponse(BaseModel):
    """历史结果响应模型"""
    model: str
    history: List[ResultItem]


def init_database():
    """初始化数据库表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            metrics_json TEXT NOT NULL
        )
    ''')
    
    # 创建索引以提高查询性能
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_model_name 
        ON evaluations(model_name)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_timestamp 
        ON evaluations(timestamp)
    ''')
    
    conn.commit()
    conn.close()


def save_to_database(model_name: str, metrics: dict) -> int:
    """
    存储评测结果到SQLite
    
    Args:
        model_name: 模型名称
        metrics: 评测指标字典
    
    Returns:
        插入的记录ID
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO evaluations (model_name, metrics_json) VALUES (?, ?)",
            (model_name, json.dumps(metrics, ensure_ascii=False))
        )
        
        evaluation_id = cursor.lastrowid
        conn.commit()
        return evaluation_id
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()


def get_results_from_database(model_name: Optional[str] = None, limit: Optional[int] = None) -> List[dict]:
    """
    从数据库获取评测结果
    
    Args:
        model_name: 可选的模型名称过滤
        limit: 可选的返回结果数量限制
    
    Returns:
        结果列表
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        if model_name:
            cursor.execute(
                "SELECT id, model_name, timestamp, metrics_json FROM evaluations WHERE model_name = ? ORDER BY timestamp DESC",
                (model_name,)
            )
        else:
            cursor.execute(
                "SELECT id, model_name, timestamp, metrics_json FROM evaluations ORDER BY timestamp DESC"
            )
        
        if limit:
            results = cursor.fetchmany(limit)
        else:
            results = cursor.fetchall()
        
        # 转换为字典列表
        result_list = []
        for row in results:
            result_list.append({
                "id": row[0],
                "model_name": row[1],
                "timestamp": row[2],
                "metrics": json.loads(row[3]),
            })
        
        return result_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()


# 启动时初始化数据库
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    init_database()


@app.get("/")
async def root():
    """根路径，返回API信息"""
    return {
        "name": "DF-LCA AI Benchmark API (Simple)",
        "version": "1.0.0",
        "description": "简化版评测API，使用 SimpleEvaluator 和 SQLite",
        "endpoints": {
            "POST /evaluate": "执行模型评测（自动发布到排行榜）",
            "GET /results": "获取所有评测结果",
            "GET /results/{model_name}": "获取指定模型的历史评测结果",
            "GET /results/{evaluation_id}/report": "生成报告（支持多种模板）",
            "GET /templates": "列出所有可用的报告模板",
            "GET /leaderboard": "获取排行榜",
            "GET /leaderboard/models/{model_name}": "获取模型统计信息",
            "POST /leaderboard/publish": "手动发布评测结果到排行榜",
            "GET /health": "健康检查",
        },
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "database": "connected" if DB_PATH.exists() else "not_found",
        "evaluator": "ready",
    }


@app.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_model(
    request: EvaluationRequest,
    publish_to_leaderboard: bool = Query(True, description="是否发布到排行榜"),
):
    """
    评测API端点
    
    执行模型评测并存储结果到数据库。
    
    Args:
        request: 评测请求，包含模型名称、任务列表和API端点
    
    Returns:
        评测结果，包含状态、模型名称、指标和评测ID
    """
    try:
        # 执行评测
        metrics = evaluator.evaluate_model(
            request.model_endpoint,
            request.tasks
        )
        
        # 存储结果
        evaluation_id = save_to_database(request.model_name, metrics)
        
        # 发布到排行榜（如果启用）
        leaderboard_info = None
        if publish_to_leaderboard:
            try:
                leaderboard_info = leaderboard.publish_results(
                    {
                        "model_name": request.model_name,
                        "task_name": ",".join(request.tasks),
                        "metrics": metrics,
                    },
                    make_public=True,
                    evaluation_id=evaluation_id,
                )
            except Exception as e:
                # 排行榜发布失败不影响评测结果
                import warnings
                warnings.warn(f"Failed to publish to leaderboard: {e}")
        
        return EvaluationResponse(
            status="success",
            model=request.model_name,
            metrics=metrics,
            evaluation_id=evaluation_id,
            leaderboard=leaderboard_info,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@app.get("/results", response_model=List[ResultItem])
async def get_all_results(limit: Optional[int] = None):
    """
    获取所有历史评测结果
    
    Args:
        limit: 可选的结果数量限制
    
    Returns:
        所有评测结果列表
    """
    try:
        results = get_results_from_database(limit=limit)
        return [
            ResultItem(
                id=r["id"],
                model_name=r["model_name"],
                timestamp=r["timestamp"],
                metrics=r["metrics"],
            )
            for r in results
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve results: {str(e)}")


@app.get("/results/{model_name}", response_model=ResultsResponse)
async def get_results(model_name: str, limit: Optional[int] = None):
    """
    获取指定模型的历史评测结果
    
    Args:
        model_name: 模型名称
        limit: 可选的结果数量限制
    
    Returns:
        指定模型的评测历史
    """
    try:
        results = get_results_from_database(model_name=model_name, limit=limit)
        
        return ResultsResponse(
            model=model_name,
            history=[
                ResultItem(
                    id=r["id"],
                    model_name=r["model_name"],
                    timestamp=r["timestamp"],
                    metrics=r["metrics"],
                )
                for r in results
            ],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve results: {str(e)}")


@app.get("/models")
async def list_models():
    """
    列出所有已评测的模型
    
    Returns:
        模型名称列表
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT model_name FROM evaluations ORDER BY model_name")
        models = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            "models": models,
            "count": len(models),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")


@app.get("/badge/score/{score}")
async def get_score_badge(
    score: float = Query(..., description="分数（0-100）"),
    color: Optional[str] = Query(None, description="颜色（blue, green, yellow, orange, red等）"),
):
    """
    生成分数徽章
    
    Args:
        score: 分数（0-100）
        color: 可选的颜色
    
    Returns:
        SVG 格式的徽章
    """
    svg = generate_score_badge(score, color)
    return Response(content=svg, media_type="image/svg+xml")


@app.get("/badge/efficiency/{grade}")
async def get_efficiency_badge(
    grade: str = Query(..., description="能效等级（A+, A, B, C, D等）"),
    color: Optional[str] = Query(None, description="颜色"),
):
    """
    生成能效等级徽章
    
    Args:
        grade: 能效等级
        color: 可选的颜色
    
    Returns:
        SVG 格式的徽章
    """
    svg = generate_efficiency_badge(grade, color)
    return Response(content=svg, media_type="image/svg+xml")


@app.get("/badge/performance/{latency_ms}")
async def get_performance_badge(
    latency_ms: float = Query(..., description="延迟（毫秒）"),
    color: Optional[str] = Query(None, description="颜色"),
):
    """
    生成性能徽章（基于延迟）
    
    Args:
        latency_ms: 延迟（毫秒）
        color: 可选的颜色
    
    Returns:
        SVG 格式的徽章
    """
    svg = generate_performance_badge(latency_ms, color)
    return Response(content=svg, media_type="image/svg+xml")


@app.get("/badge/carbon/{carbon_gco2e}")
async def get_carbon_badge(
    carbon_gco2e: float = Query(..., description="碳排放量（gCO2e）"),
    color: Optional[str] = Query(None, description="颜色"),
):
    """
    生成碳排放徽章
    
    Args:
        carbon_gco2e: 碳排放量（gCO2e）
        color: 可选的颜色
    
    Returns:
        SVG 格式的徽章
    """
    svg = generate_carbon_badge(carbon_gco2e, color)
    return Response(content=svg, media_type="image/svg+xml")


@app.get("/badge/model/{model_name}")
async def get_model_badge(
    model_name: str = Query(..., description="模型名称"),
    score: Optional[float] = Query(None, description="可选的综合得分"),
):
    """
    生成模型评测徽章
    
    Args:
        model_name: 模型名称
        score: 可选的综合得分
    
    Returns:
        SVG 格式的徽章
    """
    svg = generate_model_badge(model_name, score)
    return Response(content=svg, media_type="image/svg+xml")


@app.get("/badge/custom")
async def get_custom_badge(
    label: str = Query(..., description="左侧标签"),
    message: str = Query(..., description="右侧消息"),
    color: str = Query("blue", description="颜色"),
    style: str = Query("flat", description="样式（flat, plastic, flat-square）"),
):
    """
    生成自定义徽章
    
    Args:
        label: 左侧标签文本
        message: 右侧消息文本
        color: 徽章颜色
        style: 样式
    
    Returns:
        SVG 格式的徽章
    """
    svg = generate_badge(label, message, color, style)
    return Response(content=svg, media_type="image/svg+xml")


@app.get("/badge/result/{evaluation_id}")
async def get_result_badge(evaluation_id: int):
    """
    根据评测结果ID生成徽章
    
    Args:
        evaluation_id: 评测结果ID
    
    Returns:
        包含多个徽章的HTML页面
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT model_name, metrics_json FROM evaluations WHERE id = ?",
            (evaluation_id,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Evaluation {evaluation_id} not found")
        
        model_name, metrics_json = row
        metrics = json.loads(metrics_json)
        
        # 生成各种徽章
        badges = {}
        
        # 性能徽章
        if "performance" in metrics and metrics["performance"].get("latency_ms"):
            badges["performance"] = generate_performance_badge(
                metrics["performance"]["latency_ms"]
            )
        
        # 能效徽章（基于CPU使用率）
        if "efficiency" in metrics:
            cpu_usage = metrics["efficiency"].get("cpu_usage", 0)
            if cpu_usage < 30:
                grade = "A+"
            elif cpu_usage < 50:
                grade = "A"
            elif cpu_usage < 70:
                grade = "B"
            else:
                grade = "C"
            badges["efficiency"] = generate_efficiency_badge(grade)
        
        # 碳排放徽章
        if "carbon" in metrics and metrics["carbon"].get("carbon_footprint_g"):
            badges["carbon"] = generate_carbon_badge(
                metrics["carbon"]["carbon_footprint_g"]
            )
        
        # 模型徽章（如果有综合得分）
        # 这里简化处理，实际可以从 metrics 中计算综合得分
        badges["model"] = generate_model_badge(model_name)
        
        # 返回HTML页面展示所有徽章
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Badges for {model_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 20px; }}
        .badge-container {{ margin: 20px 0; }}
        h2 {{ margin-top: 30px; }}
        code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }}
    </style>
</head>
<body>
    <h1>Badges for {model_name}</h1>
    <p>Evaluation ID: {evaluation_id}</p>
    
    <h2>Markdown Code</h2>
    <pre><code>"""
        
        for badge_type, svg in badges.items():
            html += f'\n![{badge_type}](http://localhost:8000/badge/{badge_type}/...)'
        
        html += """
    </code></pre>
    
    <h2>Preview</h2>"""
        
        for badge_type, svg in badges.items():
            html += f'\n    <div class="badge-container">\n        <h3>{badge_type.title()}</h3>\n        {svg}\n    </div>'
        
        html += """
</body>
</html>"""
        
        return Response(content=html, media_type="text/html")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate badges: {str(e)}")


@app.get("/leaderboard")
async def get_leaderboard(
    task_name: Optional[str] = Query(None, description="任务名称过滤"),
    limit: int = Query(100, description="返回结果数量限制"),
    include_private: bool = Query(False, description="是否包含私有记录"),
):
    """
    获取排行榜
    
    Args:
        task_name: 可选的任务名称过滤
        limit: 返回结果数量限制
        include_private: 是否包含私有记录
    
    Returns:
        排行榜条目列表
    """
    try:
        entries = leaderboard.get_leaderboard(
            task_name=task_name,
            limit=limit,
            include_private=include_private,
        )
        return {
            "task_name": task_name,
            "total": len(entries),
            "entries": entries,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get leaderboard: {str(e)}")


@app.get("/leaderboard/models/{model_name}")
async def get_model_stats(model_name: str):
    """
    获取模型的统计信息
    
    Args:
        model_name: 模型名称
    
    Returns:
        模型统计信息
    """
    try:
        stats = leaderboard.get_model_stats(model_name)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model stats: {str(e)}")


@app.post("/leaderboard/publish")
async def publish_to_leaderboard(
    evaluation_id: int = Query(..., description="评测结果ID"),
    make_public: bool = Query(True, description="是否公开"),
):
    """
    手动发布评测结果到排行榜
    
    Args:
        evaluation_id: 评测结果ID
        make_public: 是否公开
    
    Returns:
        发布结果
    """
    try:
        # 从数据库获取评测结果
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT model_name, metrics_json FROM evaluations WHERE id = ?",
            (evaluation_id,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Evaluation {evaluation_id} not found")
        
        model_name, metrics_json = row
        metrics = json.loads(metrics_json)
        
        # 发布到排行榜
        result = leaderboard.publish_results(
            {
                "model_name": model_name,
                "task_name": "general",  # 可以从 metrics 中提取
                "metrics": metrics,
            },
            make_public=make_public,
            evaluation_id=evaluation_id,
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish to leaderboard: {str(e)}")


@app.get("/templates")
async def list_templates():
    """
    列出所有可用的报告模板
    
    Returns:
        模板列表
    """
    return {
        "templates": REPORT_TEMPLATES,
        "default": "engineering",
    }


@app.get("/results/{evaluation_id}/report")
async def generate_report(
    evaluation_id: int,
    template: str = Query("engineering", description="报告模板（academic, engineering, executive, sustainability）"),
    format: str = Query("html", description="输出格式（html 或 pdf）"),
):
    """
    为评测结果生成报告
    
    Args:
        evaluation_id: 评测结果ID
        template: 报告模板
        format: 输出格式
    
    Returns:
        HTML 或 PDF 报告
    """
    try:
        # 从数据库获取评测结果
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT model_name, metrics_json, timestamp FROM evaluations WHERE id = ?",
            (evaluation_id,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Evaluation {evaluation_id} not found")
        
        model_name, metrics_json, timestamp = row
        metrics = json.loads(metrics_json)
        
        # 转换为 EvaluationResult 格式
        from datetime import datetime, timezone
        from core.schemas import ModelConfig, ModelProvider, RunMetrics, PerformanceMetrics, EnergyMetrics, ValueMetrics
        
        result = EvaluationResult(
            run_id=str(evaluation_id),
            created_at=datetime.fromisoformat(timestamp.replace(" ", "T")) if isinstance(timestamp, str) else datetime.now(timezone.utc),
            task_name="general",
            model=ModelConfig(provider=ModelProvider.local, model=model_name),
            input={"prompt": "evaluated"},
            output={"text": "evaluated"},
            metrics=RunMetrics(
                performance=PerformanceMetrics(
                    latency_ms=metrics.get("performance", {}).get("latency_ms"),
                    throughput_tokens_per_s=metrics.get("performance", {}).get("throughput_tokens_per_s"),
                    accuracy=metrics.get("performance", {}).get("accuracy"),
                ),
                energy=EnergyMetrics(
                    energy_joules=metrics.get("energy", {}).get("energy_joules") or metrics.get("carbon", {}).get("estimated_energy_joules"),
                    average_power_watts=metrics.get("efficiency", {}).get("avg_power_watts"),
                    carbon_gco2e=metrics.get("carbon", {}).get("carbon_footprint_g"),
                ),
                value=ValueMetrics(),
            ),
        )
        
        # 生成报告
        generator = ReportGenerator(template=template)
        report_path = generator.generate_report(
            result,
            format=format,
            include_charts=True,
        )
        
        # 读取生成的文件
        report_content = Path(report_path).read_text(encoding="utf-8")
        
        # 删除临时文件（可选）
        # Path(report_path).unlink()
        
        if format == "pdf":
            return Response(content=report_content, media_type="application/pdf")
        else:
            return Response(content=report_content, media_type="text/html")
            
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@app.delete("/results/{evaluation_id}")
async def delete_result(evaluation_id: int):
    """
    删除指定的评测结果
    
    Args:
        evaluation_id: 评测结果ID
    
    Returns:
        删除状态
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM evaluations WHERE id = ?", (evaluation_id,))
        
        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Evaluation {evaluation_id} not found")
        
        conn.commit()
        conn.close()
        
        return {
            "status": "success",
            "message": f"Evaluation {evaluation_id} deleted",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete result: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

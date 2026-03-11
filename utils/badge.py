"""Badge Generator - 生成评测结果徽章（SVG格式）"""
from typing import Literal, Optional
from urllib.parse import quote


# 颜色方案
COLORS = {
    "blue": "#007ec6",
    "green": "#4c1",
    "yellow": "#dfb317",
    "orange": "#fe7d37",
    "red": "#e05d44",
    "brightgreen": "#4c1",
    "yellowgreen": "#a4a61d",
    "red": "#e05d44",
    "lightgrey": "#9f9f9f",
    "blue": "#007ec6",
}

# 默认样式
DEFAULT_STYLE = {
    "width": 100,
    "height": 20,
    "font_size": 11,
    "font_family": "DejaVu Sans,Verdana,Geneva,sans-serif",
}


def generate_badge(
    label: str,
    message: str,
    color: str = "blue",
    style: str = "flat",
    logo: Optional[str] = None,
) -> str:
    """
    生成 SVG 格式的徽章
    
    Args:
        label: 左侧标签文本
        message: 右侧消息文本
        color: 徽章颜色（blue, green, yellow, orange, red等）
        style: 样式（flat, plastic, flat-square）
        logo: 可选的 logo URL
    
    Returns:
        SVG 字符串
    """
    # 计算文本宽度（简单估算）
    label_width = len(label) * 6 + 10
    message_width = len(message) * 6 + 10
    
    # 总宽度
    total_width = label_width + message_width
    
    # 根据样式调整
    if style == "flat-square":
        height = 20
        radius = 0
    elif style == "plastic":
        height = 18
        radius = 3
    else:  # flat
        height = 20
        radius = 3
    
    # 获取颜色
    badge_color = COLORS.get(color, COLORS["blue"])
    
    # 生成 SVG
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{total_width}" height="{height}" role="img" aria-label="{label}: {message}">
  <title>{label}: {message}</title>
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r">
    <rect width="{total_width}" height="{height}" rx="{radius}" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#r)">
    <rect width="{label_width}" height="{height}" fill="#555"/>
    <rect x="{label_width}" width="{message_width}" height="{height}" fill="{badge_color}"/>
    <rect width="{total_width}" height="{height}" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
    <text x="{label_width / 2}" y="15" fill="#010101" fill-opacity=".3">{label}</text>
    <text x="{label_width / 2}" y="14">{label}</text>
    <text x="{label_width + message_width / 2}" y="15" fill="#010101" fill-opacity=".3">{message}</text>
    <text x="{label_width + message_width / 2}" y="14">{message}</text>
  </g>
</svg>'''
    
    return svg


def generate_score_badge(score: float, color: Optional[str] = None) -> str:
    """
    生成分数徽章
    
    Args:
        score: 分数（0-100）
        color: 可选的颜色，如果不提供则根据分数自动选择
    
    Returns:
        SVG 字符串
    """
    if color is None:
        if score >= 80:
            color = "brightgreen"
        elif score >= 60:
            color = "green"
        elif score >= 40:
            color = "yellowgreen"
        elif score >= 20:
            color = "yellow"
        else:
            color = "red"
    
    return generate_badge("Score", f"{score:.0f}", color=color)


def generate_efficiency_badge(grade: str, color: Optional[str] = None) -> str:
    """
    生成能效等级徽章
    
    Args:
        grade: 等级（A+, A, B, C, D等）
        color: 可选的颜色
    
    Returns:
        SVG 字符串
    """
    if color is None:
        grade_colors = {
            "A+": "brightgreen",
            "A": "green",
            "B": "yellowgreen",
            "C": "yellow",
            "D": "orange",
            "F": "red",
        }
        color = grade_colors.get(grade.upper(), "blue")
    
    return generate_badge("Efficiency", grade, color=color)


def generate_performance_badge(latency_ms: float, color: Optional[str] = None) -> str:
    """
    生成性能徽章（基于延迟）
    
    Args:
        latency_ms: 延迟（毫秒）
        color: 可选的颜色
    
    Returns:
        SVG 字符串
    """
    if color is None:
        if latency_ms < 100:
            color = "brightgreen"
        elif latency_ms < 500:
            color = "green"
        elif latency_ms < 1000:
            color = "yellow"
        else:
            color = "red"
    
    if latency_ms < 1000:
        message = f"{latency_ms:.0f}ms"
    else:
        message = f"{latency_ms/1000:.1f}s"
    
    return generate_badge("Latency", message, color=color)


def generate_carbon_badge(carbon_gco2e: float, color: Optional[str] = None) -> str:
    """
    生成碳排放徽章
    
    Args:
        carbon_gco2e: 碳排放量（gCO2e）
        color: 可选的颜色
    
    Returns:
        SVG 字符串
    """
    if color is None:
        if carbon_gco2e < 0.001:
            color = "brightgreen"
        elif carbon_gco2e < 0.01:
            color = "green"
        elif carbon_gco2e < 0.1:
            color = "yellow"
        else:
            color = "red"
    
    if carbon_gco2e < 0.001:
        message = f"{carbon_gco2e*1000:.2f}mg"
    elif carbon_gco2e < 1:
        message = f"{carbon_gco2e:.3f}g"
    else:
        message = f"{carbon_gco2e:.2f}g"
    
    return generate_badge("Carbon", message, color=color)


def generate_model_badge(model_name: str, score: Optional[float] = None) -> str:
    """
    生成模型评测徽章
    
    Args:
        model_name: 模型名称
        score: 可选的综合得分
    
    Returns:
        SVG 字符串
    """
    if score is not None:
        message = f"{score:.0f}"
        if score >= 80:
            color = "brightgreen"
        elif score >= 60:
            color = "green"
        else:
            color = "yellow"
    else:
        message = "evaluated"
        color = "blue"
    
    return generate_badge("DF-LCA", message, color=color)


def get_badge_url(
    badge_type: str,
    value: str,
    color: Optional[str] = None,
    style: str = "flat",
) -> str:
    """
    生成徽章 URL（用于在 README 中引用）
    
    Args:
        badge_type: 徽章类型（score, efficiency, performance, carbon, model）
        value: 值
        color: 可选的颜色
        style: 样式
    
    Returns:
        徽章 URL
    """
    base_url = "https://benchmark.dflca.ai/badge"
    
    if badge_type == "score":
        return f"{base_url}/score/{value}/{color or 'blue'}.svg"
    elif badge_type == "efficiency":
        return f"{base_url}/efficiency/{quote(value)}/{color or 'green'}.svg"
    elif badge_type == "performance":
        return f"{base_url}/performance/{value}/{color or 'blue'}.svg"
    elif badge_type == "carbon":
        return f"{base_url}/carbon/{value}/{color or 'green'}.svg"
    elif badge_type == "model":
        return f"{base_url}/model/{quote(value)}.svg"
    else:
        return f"{base_url}/{badge_type}/{quote(value)}/{color or 'blue'}.svg"

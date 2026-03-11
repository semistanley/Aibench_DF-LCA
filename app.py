"""Streamlit界面 - DF-LCA AI系统评测平台"""
import asyncio
from typing import Dict, Any, List

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from core.schemas import ModelConfig, ModelProvider, EvaluationRequest, EvaluationOptions, EnergyCollectionMethod
from dflca_evaluator import DFLCAEvaluator
from benchmark_tasks import BenchmarkTasks
from reporter import ReportGenerator
from models import registry


# Page config
st.set_page_config(
    page_title="DF-LCA AI系统评测平台",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📊 DF-LCA AI系统评测平台")
st.markdown("**Digital Footprint - Life Cycle Assessment for AI Model Evaluation**")

# Initialize session state
if "evaluation_results" not in st.session_state:
    st.session_state.evaluation_results = []


def run_evaluation(model_name: str, task_names: List[str]) -> Dict[str, Any]:
    """
    运行评测并返回结果。
    
    Args:
        model_name: 模型名称 (GPT-4, Claude-3, Llama-3, Gemini, OpenClaw)
        task_names: 评测任务列表 (MMLU, BBH, GSM8K, HumanEval)
    
    Returns:
        包含评测结果的字典
    """
    # 模型名称映射到实际配置
    model_mapping = {
        "GPT-4": {"provider": ModelProvider.openai, "model": "gpt-4"},
        "Claude-3": {"provider": ModelProvider.openai, "model": "claude-3"},  # 占位
        "Llama-3": {"provider": ModelProvider.huggingface, "model": "meta-llama/Meta-Llama-3-8B-Instruct"},
        "Gemini": {"provider": ModelProvider.openai, "model": "gemini"},  # 占位
        "OpenClaw": {"provider": ModelProvider.local, "model": "echo"},  # 占位
    }
    
    # 任务名称映射到实际任务标识
    task_mapping = {
        "MMLU": "mmlu",
        "BBH": "bbh",
        "GSM8K": "gsm8k",
        "HumanEval": "human_eval",
    }
    
    # 获取模型配置
    if model_name not in model_mapping:
        raise ValueError(f"Unknown model: {model_name}")
    
    model_info = model_mapping[model_name]
    model_config = ModelConfig(
        provider=model_info["provider"],
        model=model_info["model"],
    )
    
    # 加载任务数据集
    tasks = BenchmarkTasks()
    all_samples = []
    
    for task_display_name in task_names:
        if task_display_name not in task_mapping:
            continue
        
        task_id = task_mapping[task_display_name]
        try:
            # 加载少量样本进行评测（实际使用时可以增加）
            samples = tasks.load_dataset(task_id, limit=5)
            for sample in samples:
                all_samples.append({
                    "prompt": sample["prompt"],
                    "task": task_id,
                    "target": sample.get("target"),
                })
        except Exception as e:
            st.warning(f"Failed to load task {task_display_name}: {e}")
            # 如果加载失败，使用默认提示
            all_samples.append({
                "prompt": f"Sample question for {task_display_name}",
                "task": task_id,
            })
    
    if not all_samples:
        # 如果没有加载到样本，使用默认提示
        all_samples = [{"prompt": "Hello, world!", "task": "demo"}]
    
    # 运行评测
    evaluator = DFLCAEvaluator()
    result_dict = asyncio.run(evaluator.evaluate(model_config, all_samples))
    
    # 计算综合评分
    report_gen = ReportGenerator()
    # 创建一个临时的 EvaluationResult 用于评分计算
    from core.schemas import EvaluationResult, RunMetrics, PerformanceMetrics, EnergyMetrics, ValueMetrics
    from datetime import datetime, timezone
    
    # 构建临时的 EvaluationResult（用于评分计算）
    temp_result = EvaluationResult(
        run_id="temp",
        created_at=datetime.now(timezone.utc),
        task_name=",".join(task_names),
        model=model_config,
        input={"prompt": all_samples[0]["prompt"]},
        output={"text": "evaluated"},
        metrics=RunMetrics(
            performance=PerformanceMetrics(
                latency_ms=result_dict["performance"]["latency_ms"],
                throughput_tokens_per_s=result_dict["performance"]["throughput_tokens_per_s"],
                input_tokens=result_dict["performance"].get("input_tokens"),
                output_tokens=result_dict["performance"].get("output_tokens"),
            ),
            energy=EnergyMetrics(
                energy_joules=result_dict["energy"]["energy_joules"],
                average_power_watts=result_dict["energy"].get("avg_power_watts"),
                carbon_gco2e=result_dict["carbon"]["carbon_gco2e"],
            ),
            value=ValueMetrics(
                quality_score=0.85,  # 占位值
            ),
        ),
    )
    
    # 计算综合评分
    score = report_gen._calculate_overall_score(temp_result)
    
    # 计算能效比（Energy Efficiency Ratio）
    efficiency_score = score.get("energy", 0) / 25.0 * 100 if score.get("energy") else 0
    
    # 准备详细指标数据
    detailed_metrics = {
        "性能得分": score.get("performance", 0),
        "能效得分": score.get("energy", 0),
        "碳排放得分": score.get("carbon", 0),
        "价值得分": score.get("value", 0),
        "资源得分": score.get("resource", 0),
    }
    
    return {
        "overall_score": score.get("total", 0),
        "efficiency_score": efficiency_score,
        "carbon_footprint": result_dict["carbon"]["carbon_gco2e"] or 0.0,
        "detailed_metrics": detailed_metrics,
        "raw_result": result_dict,
        "score_breakdown": score,
    }


# 侧边栏 - 模型选择
st.sidebar.header("🔧 配置")

model_options = ["GPT-4", "Claude-3", "Llama-3", "Gemini", "OpenClaw"]
selected_model = st.sidebar.selectbox("选择模型", model_options, help="选择要评测的AI模型")

# 侧边栏 - 任务选择
task_options = ["MMLU", "BBH", "GSM8K", "HumanEval"]
selected_tasks = st.sidebar.multiselect(
    "选择评测任务",
    task_options,
    default=task_options[:1] if task_options else [],
    help="可以选择多个评测任务"
)

# 高级选项
with st.sidebar.expander("⚙️ 高级选项"):
    energy_method = st.selectbox(
        "能耗采集方法",
        [m.value for m in EnergyCollectionMethod],
        index=0,
        help="选择能耗数据采集方法",
    )
    
    sample_interval = st.slider(
        "采样间隔 (秒)",
        min_value=0.1,
        max_value=2.0,
        value=0.25,
        step=0.05,
        help="评测过程中的指标采样间隔",
    )

# 主界面
if st.button("🚀 开始评测", type="primary", use_container_width=True):
    if not selected_tasks:
        st.warning("⚠️ 请至少选择一个评测任务")
    else:
        with st.spinner("正在评测中，请稍候..."):
            try:
                results = run_evaluation(selected_model, selected_tasks)
                st.session_state.evaluation_results.append(results)
                
                st.success("✅ 评测完成！")
                st.balloons()
                
                # 显示结果
                st.subheader("📈 评测结果")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("综合得分", f"{results['overall_score']:.2f}", help="总分100分，基于性能、能耗、碳排放、价值和资源利用率")
                
                with col2:
                    st.metric("能效比", f"{results['efficiency_score']:.2f}%", help="能效得分百分比")
                    
                with col3:
                    st.metric("碳排放(gCO2e)", f"{results['carbon_footprint']:.6f}", help="二氧化碳当量（克）")
                
                # 图表展示
                st.subheader("📊 详细指标")
                
                # 使用 Plotly 创建柱状图
                metrics_df = pd.DataFrame([
                    {"指标": k, "得分": v}
                    for k, v in results['detailed_metrics'].items()
                ])
                
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=metrics_df["指标"],
                    y=metrics_df["得分"],
                    marker_color=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"],
                    text=metrics_df["得分"].round(2),
                    textposition="outside",
                ))
                fig.update_layout(
                    title="各维度得分对比",
                    xaxis_title="指标维度",
                    yaxis_title="得分",
                    height=400,
                    showlegend=False,
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # 使用 Streamlit 原生图表作为备选
                st.bar_chart(metrics_df.set_index("指标"))
                
                # 显示更多详细信息
                with st.expander("📋 详细数据"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**性能指标**")
                        perf = results['raw_result']['performance']
                        st.json({
                            "延迟 (ms)": perf.get("latency_ms"),
                            "吞吐量 (tokens/s)": perf.get("throughput_tokens_per_s"),
                            "输入 tokens": perf.get("input_tokens"),
                            "输出 tokens": perf.get("output_tokens"),
                        })
                    
                    with col2:
                        st.markdown("**能耗指标**")
                        energy = results['raw_result']['energy']
                        st.json({
                            "总能耗 (J)": energy.get("energy_joules"),
                            "平均功率 (W)": energy.get("avg_power_watts"),
                            "采集方法": energy.get("method", "unknown"),
                        })
                    
                    st.markdown("**评分分解**")
                    st.json(results['score_breakdown'])
                
            except Exception as e:
                st.error(f"❌ 评测失败: {str(e)}")
                st.exception(e)

# 显示历史记录
if st.session_state.evaluation_results:
    st.divider()
    st.subheader("📚 评测历史")
    
    history_data = []
    for i, r in enumerate(st.session_state.evaluation_results):
        history_data.append({
            "序号": i + 1,
            "综合得分": f"{r['overall_score']:.2f}",
            "能效比": f"{r['efficiency_score']:.2f}%",
            "碳排放(gCO2e)": f"{r['carbon_footprint']:.6f}",
        })
    
    if history_data:
        df_history = pd.DataFrame(history_data)
        st.dataframe(df_history, use_container_width=True, hide_index=True)
        
        # 清除历史按钮
        if st.button("🗑️ 清除历史"):
            st.session_state.evaluation_results = []
            st.rerun()

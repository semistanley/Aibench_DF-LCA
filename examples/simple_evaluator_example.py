"""Example: Using SimpleEvaluator for quick model evaluation."""
from simple_evaluator import SimpleEvaluator


def main():
    """Run a simple evaluation example."""
    # 创建评测器
    evaluator = SimpleEvaluator()
    
    # 配置模型端点（这里使用模拟端点）
    # 实际使用时，替换为真实的模型API端点
    model_endpoint = "http://localhost:8000/v1/completions"  # 示例端点
    
    # 选择评测任务
    tasks = ["MMLU", "GSM8K"]
    
    print("开始评测...")
    print(f"模型端点: {model_endpoint}")
    print(f"评测任务: {', '.join(tasks)}")
    print("-" * 60)
    
    # 执行评测
    try:
        metrics = evaluator.evaluate_model(model_endpoint, tasks)
        
        # 显示结果
        print("\n📊 评测结果:")
        print("-" * 60)
        
        # 性能指标
        perf = metrics["performance"]
        print(f"\n⚡ 性能指标:")
        print(f"  准确率: {perf['accuracy']:.2%}")
        print(f"  延迟: {perf['latency']:.2f} 秒 ({perf['latency_ms']:.2f} 毫秒)")
        
        # 能效指标
        eff = metrics["efficiency"]
        print(f"\n🔋 能效指标:")
        print(f"  CPU使用率: {eff['cpu_usage']:.2f}%")
        print(f"  内存使用率: {eff['memory_usage']:.2f}%")
        print(f"  吞吐量: {eff['throughput']:.2f} 任务/秒")
        
        # 碳排放指标
        carbon = metrics["carbon"]
        print(f"\n🌍 碳排放指标:")
        print(f"  估算能耗: {carbon['estimated_energy_kwh']:.6f} kWh")
        print(f"  估算能耗: {carbon['estimated_energy_joules']:.2f} J")
        print(f"  碳排放: {carbon['carbon_footprint_kg']:.6f} kgCO2e")
        print(f"  碳排放: {carbon['carbon_footprint_g']:.4f} gCO2e")
        
        # 获取所有结果
        print(f"\n📚 历史记录数量: {len(evaluator.get_results())}")
        
    except Exception as e:
        print(f"❌ 评测失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

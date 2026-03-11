"""Simple Evaluator - 核心评测逻辑（简化版）"""
import time
from typing import Dict, List, Optional

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class SimpleEvaluator:
    """
    简化的评测器，用于快速评测模型并收集DF-LCA指标。
    
    包含：
    1. 性能评测（准确率、延迟）
    2. 能效评测（CPU使用率、内存使用率、吞吐量）
    3. 碳排放估算（基于平均能耗）
    """
    
    def __init__(self):
        """初始化评测器"""
        self.results = []
        if not HAS_PSUTIL:
            import warnings
            warnings.warn("psutil not installed. Some metrics will be unavailable.")
        if not HAS_REQUESTS:
            import warnings
            warnings.warn("requests not installed. API calls will be unavailable.")
        
    def evaluate_model(self, model_endpoint: str, tasks: List[str]) -> Dict:
        """
        执行评测并收集DF-LCA指标
        
        Args:
            model_endpoint: 模型API端点URL
            tasks: 评测任务列表（如 ["MMLU", "GSM8K"]）
        
        Returns:
            包含性能、能效、碳排放指标的字典
        """
        metrics = {}
        
        # 1. 性能评测
        performance_start = time.time()
        accuracy_scores = self.run_benchmark_tasks(model_endpoint, tasks)
        performance_end = time.time()
        latency = performance_end - performance_start
        
        metrics["performance"] = {
            "accuracy": sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0.0,
            "latency": latency,
            "latency_ms": latency * 1000,
        }
        
        # 2. 能效评测（简化版）
        if HAS_PSUTIL:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_usage = psutil.virtual_memory().percent
        else:
            cpu_percent = 0.0
            memory_usage = 0.0
        
        throughput = len(tasks) / latency if latency > 0 else 0
        
        metrics["efficiency"] = {
            "cpu_usage": cpu_percent,
            "memory_usage": memory_usage,
            "throughput": throughput,
            "throughput_tasks_per_s": throughput,
        }
        
        # 3. 碳排放估算（基于平均能耗）
        # 简化公式: 能耗(kWh) = (CPU使用率 * TDP) * 时间 / 1000
        # 假设TDP为65W（典型CPU功耗）
        tdp_watts = 65.0  # 典型CPU TDP
        estimated_energy_kwh = (cpu_percent / 100 * tdp_watts) * latency / 3600
        estimated_energy_joules = estimated_energy_kwh * 3.6e6  # 转换为焦耳
        
        # 假设碳排放因子为 0.5 kgCO2/kWh（全球平均）
        carbon_intensity_kgco2_per_kwh = 0.5
        carbon_footprint_kg = estimated_energy_kwh * carbon_intensity_kgco2_per_kwh
        carbon_footprint_g = carbon_footprint_kg * 1000  # 转换为克
        
        metrics["carbon"] = {
            "estimated_energy_kwh": estimated_energy_kwh,
            "estimated_energy_joules": estimated_energy_joules,
            "carbon_footprint_kg": carbon_footprint_kg,
            "carbon_footprint_g": carbon_footprint_g,
            "carbon_footprint_gco2e": carbon_footprint_g,  # 简化假设 gCO2e = gCO2
        }
        
        # 保存结果
        result = {
            "model_endpoint": model_endpoint,
            "tasks": tasks,
            "metrics": metrics,
            "timestamp": time.time(),
        }
        self.results.append(result)
        
        return metrics
    
    def run_benchmark_tasks(self, model_endpoint: str, tasks: List[str]) -> List[float]:
        """
        运行具体的评测任务
        
        Args:
            model_endpoint: 模型API端点
            tasks: 任务列表
        
        Returns:
            每个任务的准确率分数列表
        """
        scores = []
        
        for task in tasks:
            if task == "MMLU":
                score = self.evaluate_mmlu(model_endpoint)
            elif task == "GSM8K":
                score = self.evaluate_gsm8k(model_endpoint)
            elif task == "BBH":
                score = self.evaluate_bbh(model_endpoint)
            elif task == "HumanEval":
                score = self.evaluate_humaneval(model_endpoint)
            else:
                # 未知任务，返回默认分数
                score = 0.5
                import warnings
                warnings.warn(f"Unknown task: {task}, using default score 0.5")
            
            scores.append(score)
        
        return scores
    
    def evaluate_mmlu(self, model_endpoint: str) -> float:
        """
        简化的MMLU评测
        
        Args:
            model_endpoint: 模型API端点
        
        Returns:
            准确率分数（0-1）
        """
        # 实际应使用完整的MMLU数据集
        test_questions = [
            {"question": "What is 2+2?", "options": ["3", "4", "5", "6"], "answer": "4"},
            {"question": "What is the capital of France?", "options": ["London", "Berlin", "Paris", "Madrid"], "answer": "Paris"},
        ]
        
        correct = 0
        total = len(test_questions)
        
        for q in test_questions:
            try:
                response = self.call_model(model_endpoint, q["question"])
                # 简单匹配：检查答案是否在响应中
                if q["answer"].lower() in response.lower():
                    correct += 1
            except Exception as e:
                import warnings
                warnings.warn(f"Error evaluating MMLU question: {e}")
        
        return correct / total if total > 0 else 0.0
    
    def evaluate_gsm8k(self, model_endpoint: str) -> float:
        """
        简化的GSM8K评测（数学问题）
        
        Args:
            model_endpoint: 模型API端点
        
        Returns:
            准确率分数（0-1）
        """
        test_questions = [
            {"question": "Janet has 5 apples. She gives 2 to Bob. How many does she have left?", "answer": "3"},
            {"question": "A store has 20 books. They sell 8. How many remain?", "answer": "12"},
        ]
        
        correct = 0
        total = len(test_questions)
        
        for q in test_questions:
            try:
                response = self.call_model(model_endpoint, q["question"])
                # 提取数字并比较
                import re
                numbers = re.findall(r'\d+', response)
                if numbers and numbers[0] == q["answer"]:
                    correct += 1
            except Exception as e:
                import warnings
                warnings.warn(f"Error evaluating GSM8K question: {e}")
        
        return correct / total if total > 0 else 0.0
    
    def evaluate_bbh(self, model_endpoint: str) -> float:
        """
        简化的BBH（Big Bench Hard）评测
        
        Args:
            model_endpoint: 模型API端点
        
        Returns:
            准确率分数（0-1）
        """
        # 占位实现
        return 0.5
    
    def evaluate_humaneval(self, model_endpoint: str) -> float:
        """
        简化的HumanEval（代码生成）评测
        
        Args:
            model_endpoint: 模型API端点
        
        Returns:
            准确率分数（0-1）
        """
        # 占位实现
        return 0.5
    
    def call_model(self, endpoint: str, prompt: str, timeout: int = 30) -> str:
        """
        调用模型API
        
        Args:
            endpoint: API端点URL
            prompt: 输入提示
            timeout: 超时时间（秒）
        
        Returns:
            模型响应文本
        """
        if not HAS_REQUESTS:
            # 如果 requests 不可用，返回模拟响应
            return "模拟响应（requests库未安装）"
        
        try:
            # 这里根据实际API格式调整
            # 支持 OpenAI 兼容格式
            response = requests.post(
                endpoint,
                json={
                    "prompt": prompt,
                    "max_tokens": 50,
                    "temperature": 0.7,
                },
                timeout=timeout,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            
            data = response.json()
            
            # 尝试不同的响应格式
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0].get("text", "")
            elif "text" in data:
                return data["text"]
            elif "response" in data:
                return data["response"]
            else:
                return str(data)
                
        except requests.exceptions.RequestException as e:
            import warnings
            warnings.warn(f"API call failed: {e}. Returning mock response.")
            return "模拟响应（API调用失败）"
        except Exception as e:
            import warnings
            warnings.warn(f"Unexpected error: {e}. Returning mock response.")
            return "模拟响应（未知错误）"
    
    def get_results(self) -> List[Dict]:
        """
        获取所有评测结果
        
        Returns:
            评测结果列表
        """
        return self.results
    
    def clear_results(self):
        """清除所有评测结果"""
        self.results = []

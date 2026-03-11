"""Evaluator Entry Point - Provides both simple and full DF-LCA evaluators."""
from dflca_evaluator import DFLCAEvaluator, evaluate
from simple_evaluator import SimpleEvaluator

__all__ = ["DFLCAEvaluator", "evaluate", "SimpleEvaluator"]

# This file provides entry points for both evaluators:
# 
# 1. SimpleEvaluator - 简化版评测器（快速评测）
#    Usage:
#      from evaluator import SimpleEvaluator
#      eval = SimpleEvaluator()
#      metrics = eval.evaluate_model("http://api.example.com", ["MMLU", "GSM8K"])
#
# 2. DFLCAEvaluator - 完整版DF-LCA评测器（5个核心维度）
#    Usage:
#      from evaluator import DFLCAEvaluator
#      eval = DFLCAEvaluator()
#      result = await eval.evaluate(model_config, tasks)

"""Benchmark Tasks Management - Standard evaluation datasets and task definitions."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from datasets import load_dataset, Dataset
    HAS_DATASETS = True
except ImportError:
    HAS_DATASETS = False
    Dataset = Any


class BenchmarkTasks:
    """
    Manages benchmark tasks and dataset loading for DF-LCA evaluation.
    
    Task categories:
    - reasoning: MMLU, BBH, GSM8K
    - coding: HumanEval, MBPP
    - knowledge: TriviaQA, Natural Questions
    - openclaw_specific: Tool usage, API calling, Workflow execution
    """

    tasks = {
        "reasoning": ["mmlu", "bbh", "gsm8k"],
        "coding": ["human_eval", "mbpp"],
        "knowledge": ["triviaqa", "natural_questions"],
        "openclaw_specific": ["tool_usage", "api_calling", "workflow_execution"],
    }

    # Dataset loading configurations
    _dataset_configs: Dict[str, Dict[str, Any]] = {
        "mmlu": {
            "hf_path": "cais/mmlu",
            "subset": "all",
            "split": "test",
            "prompt_field": "question",
            "answer_field": "choices",
            "target_field": "answer",
        },
        "bbh": {
            "hf_path": "lukaemon/bbh",
            "subset": None,
            "split": "test",
            "prompt_field": "input",
            "answer_field": None,
            "target_field": "target",
        },
        "gsm8k": {
            "hf_path": "gsm8k",
            "subset": "main",
            "split": "test",
            "prompt_field": "question",
            "answer_field": None,
            "target_field": "answer",
        },
        "human_eval": {
            "hf_path": "openai/humaneval",
            "subset": None,
            "split": "test",
            "prompt_field": "prompt",
            "answer_field": None,
            "target_field": "canonical_solution",
        },
        "mbpp": {
            "hf_path": "mbpp",
            "subset": None,
            "split": "test",
            "prompt_field": "text",
            "answer_field": None,
            "target_field": "code",
        },
        "triviaqa": {
            "hf_path": "trivia_qa",
            "subset": "rc",
            "split": "validation",
            "prompt_field": "question",
            "answer_field": "answer",
            "target_field": "answer",
        },
        "natural_questions": {
            "hf_path": "natural_questions",
            "subset": None,
            "split": "validation",
            "prompt_field": "question",
            "answer_field": "answers",
            "target_field": "answers",
        },
        # Custom/placeholder tasks
        "tool_usage": {
            "hf_path": None,
            "local_path": "data/tool_usage.json",
            "prompt_field": "instruction",
            "answer_field": None,
            "target_field": "expected_output",
        },
        "api_calling": {
            "hf_path": None,
            "local_path": "data/api_calling.json",
            "prompt_field": "api_request",
            "answer_field": None,
            "target_field": "expected_response",
        },
        "workflow_execution": {
            "hf_path": None,
            "local_path": "data/workflow_execution.json",
            "prompt_field": "workflow",
            "answer_field": None,
            "target_field": "expected_result",
        },
    }

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize BenchmarkTasks.

        Args:
            cache_dir: Directory to cache downloaded datasets (default: ~/.cache/huggingface/datasets)
        """
        self.cache_dir = cache_dir
        if not HAS_DATASETS:
            import warnings
            warnings.warn(
                "datasets library not installed. Install with: pip install datasets\n"
                "Some dataset loading features will be limited.",
                ImportWarning,
            )

    def list_tasks(self, category: Optional[str] = None) -> List[str]:
        """
        List available tasks.

        Args:
            category: Optional category filter (reasoning, coding, knowledge, openclaw_specific)

        Returns:
            List of task names
        """
        if category:
            return self.tasks.get(category, [])
        return [task for tasks in self.tasks.values() for task in tasks]

    def list_categories(self) -> List[str]:
        """List available task categories."""
        return list(self.tasks.keys())

    def get_task_category(self, task_name: str) -> Optional[str]:
        """Get the category for a given task name."""
        for category, tasks in self.tasks.items():
            if task_name in tasks:
                return category
        return None

    def load_dataset(
        self,
        task_name: str,
        *,
        split: Optional[str] = None,
        limit: Optional[int] = None,
        shuffle: bool = False,
        seed: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Load a standard benchmark dataset.

        Args:
            task_name: Name of the task (e.g., "mmlu", "gsm8k", "human_eval")
            split: Dataset split to load (default: from config)
            limit: Maximum number of samples to load (None = all)
            shuffle: Whether to shuffle the dataset
            seed: Random seed for shuffling

        Returns:
            List of task samples, each with 'prompt' and optionally 'target' fields

        Raises:
            ValueError: If task_name is not recognized
            ImportError: If datasets library is not available and task requires it
        """
        if task_name not in self._dataset_configs:
            raise ValueError(
                f"Unknown task: {task_name}. Available tasks: {self.list_tasks()}"
            )

        config = self._dataset_configs[task_name]
        split = split or config.get("split", "test")

        # Handle local/custom datasets
        if config.get("hf_path") is None:
            return self._load_local_dataset(task_name, config, limit=limit, shuffle=shuffle, seed=seed)

        # Handle HuggingFace datasets
        if not HAS_DATASETS:
            raise ImportError(
                "datasets library required for loading HuggingFace datasets. "
                "Install with: pip install datasets"
            )

        try:
            hf_path = config["hf_path"]
            subset = config.get("subset")
            kwargs = {}
            if self.cache_dir:
                kwargs["cache_dir"] = self.cache_dir

            if subset:
                dataset = load_dataset(hf_path, subset, split=split, **kwargs)
            else:
                dataset = load_dataset(hf_path, split=split, **kwargs)

            # Convert to list of dicts
            samples = []
            prompt_field = config["prompt_field"]
            target_field = config.get("target_field")
            answer_field = config.get("answer_field")

            for item in dataset:
                sample = {
                    "prompt": self._extract_field(item, prompt_field),
                    "task": task_name,
                }

                # Add target/ground truth if available
                if target_field:
                    sample["target"] = self._extract_field(item, target_field)

                # Add answer choices if available (for multiple choice)
                if answer_field:
                    sample["choices"] = self._extract_field(item, answer_field)

                # Preserve original item metadata
                sample["_metadata"] = {k: v for k, v in item.items() if k not in [prompt_field, target_field, answer_field]}

                samples.append(sample)

            # Apply shuffling
            if shuffle:
                import random
                if seed is not None:
                    random.seed(seed)
                random.shuffle(samples)

            # Apply limit
            if limit:
                samples = samples[:limit]

            return samples

        except Exception as e:
            raise RuntimeError(f"Failed to load dataset for task '{task_name}': {e}") from e

    def _load_local_dataset(
        self,
        task_name: str,
        config: Dict[str, Any],
        *,
        limit: Optional[int] = None,
        shuffle: bool = False,
        seed: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Load dataset from local JSON file."""
        local_path = config.get("local_path")
        if not local_path:
            raise ValueError(f"No local path configured for task '{task_name}'")

        path = Path(local_path)
        if not path.exists():
            # Try relative to project root
            path = Path(__file__).parent / local_path
            if not path.exists():
                raise FileNotFoundError(
                    f"Local dataset file not found for task '{task_name}': {local_path}"
                )

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Handle different JSON structures
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict) and "samples" in data:
                items = data["samples"]
            elif isinstance(data, dict) and "data" in data:
                items = data["data"]
            else:
                items = [data]

            prompt_field = config["prompt_field"]
            target_field = config.get("target_field")

            samples = []
            for item in items:
                sample = {
                    "prompt": self._extract_field(item, prompt_field),
                    "task": task_name,
                }

                if target_field:
                    sample["target"] = self._extract_field(item, target_field)

                sample["_metadata"] = {k: v for k, v in item.items() if k not in [prompt_field, target_field]}

                samples.append(sample)

            if shuffle:
                import random
                if seed is not None:
                    random.seed(seed)
                random.shuffle(samples)

            if limit:
                samples = samples[:limit]

            return samples

        except Exception as e:
            raise RuntimeError(f"Failed to load local dataset for task '{task_name}': {e}") from e

    def _extract_field(self, item: Dict[str, Any], field: str) -> Any:
        """Extract field from item, handling nested paths."""
        if "." in field:
            parts = field.split(".")
            value = item
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                elif isinstance(value, list) and part.isdigit():
                    value = value[int(part)]
                else:
                    return None
            return value
        return item.get(field)

    def get_task_info(self, task_name: str) -> Dict[str, Any]:
        """
        Get information about a task.

        Args:
            task_name: Name of the task

        Returns:
            Dictionary with task information
        """
        if task_name not in self._dataset_configs:
            raise ValueError(f"Unknown task: {task_name}")

        config = self._dataset_configs[task_name]
        category = self.get_task_category(task_name)

        return {
            "name": task_name,
            "category": category,
            "hf_path": config.get("hf_path"),
            "local_path": config.get("local_path"),
            "split": config.get("split"),
            "prompt_field": config.get("prompt_field"),
            "target_field": config.get("target_field"),
            "answer_field": config.get("answer_field"),
        }

    def create_evaluation_request(
        self,
        task_name: str,
        model_config: Any,
        *,
        limit: Optional[int] = None,
        sample_index: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Create evaluation requests from a task dataset.

        Args:
            task_name: Name of the task
            model_config: Model configuration (ModelConfig or dict)
            limit: Maximum number of samples (None = all)
            sample_index: Specific sample index to evaluate (None = all)

        Returns:
            List of evaluation request dictionaries
        """
        from core.schemas import EvaluationRequest

        samples = self.load_dataset(task_name, limit=limit)

        if sample_index is not None:
            if sample_index >= len(samples):
                raise IndexError(f"Sample index {sample_index} out of range (max: {len(samples) - 1})")
            samples = [samples[sample_index]]

        requests = []
        for i, sample in enumerate(samples):
            req = {
                "task_name": f"{task_name}_{i}",
                "input": {"prompt": sample["prompt"]},
                "model": model_config,
                "tags": {
                    "task": task_name,
                    "sample_index": str(i),
                },
            }

            # Add target if available
            if "target" in sample:
                req["tags"]["target"] = str(sample["target"])

            requests.append(req)

        return requests


# Global instance for convenience
benchmark_tasks = BenchmarkTasks()

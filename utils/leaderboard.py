"""Leaderboard - 排行榜系统"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from core.schemas import EvaluationResult


class Leaderboard:
    """
    排行榜系统 - 管理评测结果的排名和发布
    """
    
    def __init__(self, db_path: str = "leaderboard.db"):
        """
        初始化排行榜
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建排行榜表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leaderboard (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                model_provider TEXT,
                task_name TEXT,
                score REAL,
                performance_score REAL,
                efficiency_score REAL,
                carbon_score REAL,
                latency_ms REAL,
                energy_joules REAL,
                carbon_gco2e REAL,
                accuracy REAL,
                throughput_tokens_per_s REAL,
                is_public INTEGER DEFAULT 1,
                submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                evaluation_id INTEGER,
                metadata_json TEXT,
                UNIQUE(model_name, task_name, submitted_at)
            )
        ''')
        
        # 创建索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_model_name 
            ON leaderboard(model_name)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_score 
            ON leaderboard(score DESC)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_is_public 
            ON leaderboard(is_public)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_submitted_at 
            ON leaderboard(submitted_at DESC)
        ''')
        
        conn.commit()
        conn.close()
    
    def publish_results(
        self,
        results: Dict[str, Any],
        make_public: bool = True,
        evaluation_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        发布结果到排行榜
        
        Args:
            results: 评测结果字典，包含：
                - model_name: 模型名称
                - model_provider: 模型提供商（可选）
                - task_name: 任务名称（可选）
                - metrics: 指标字典
            make_public: 是否公开（默认True）
            evaluation_id: 关联的评测ID（可选）
        
        Returns:
            包含排行榜URL、排名、百分位数的字典
        """
        # 提取信息
        model_name = results.get("model_name", "unknown")
        model_provider = results.get("model_provider")
        task_name = results.get("task_name", "general")
        metrics = results.get("metrics", {})
        
        # 计算综合得分（如果有）
        score = self._calculate_overall_score(metrics)
        
        # 提取各项指标
        performance = metrics.get("performance", {})
        efficiency = metrics.get("efficiency", {})
        carbon = metrics.get("carbon", {})
        
        performance_score = performance.get("accuracy", 0) * 100 if performance.get("accuracy") else None
        efficiency_score = efficiency.get("cpu_usage", 0)  # 可以转换为得分
        carbon_score = carbon.get("carbon_footprint_g", 0)
        
        latency_ms = performance.get("latency_ms")
        energy_joules = efficiency.get("energy_joules") or carbon.get("estimated_energy_joules")
        carbon_gco2e = carbon.get("carbon_footprint_g")
        accuracy = performance.get("accuracy")
        throughput = performance.get("throughput_tokens_per_s")
        
        # 存储到数据库
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            metadata = {
                "full_metrics": metrics,
                "submitted_at": datetime.now().isoformat(),
            }
            
            cursor.execute('''
                INSERT INTO leaderboard (
                    model_name, model_provider, task_name,
                    score, performance_score, efficiency_score, carbon_score,
                    latency_ms, energy_joules, carbon_gco2e,
                    accuracy, throughput_tokens_per_s,
                    is_public, evaluation_id, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                model_name,
                model_provider,
                task_name,
                score,
                performance_score,
                efficiency_score,
                carbon_score,
                latency_ms,
                energy_joules,
                carbon_gco2e,
                accuracy,
                throughput,
                1 if make_public else 0,
                evaluation_id,
                json.dumps(metadata, ensure_ascii=False),
            ))
            
            entry_id = cursor.lastrowid
            conn.commit()
            
            # 计算排名和百分位数
            rank_info = self._calculate_rank(model_name, task_name, score)
            
            return {
                "leaderboard_url": f"https://benchmark.dflca.ai/leaderboard",
                "model_url": f"https://benchmark.dflca.ai/models/{model_name}",
                "entry_id": entry_id,
                "rank": rank_info["rank"],
                "total_entries": rank_info["total"],
                "percentile": rank_info["percentile"],
                "is_public": make_public,
            }
        except sqlite3.IntegrityError:
            conn.rollback()
            # 如果已存在，更新记录
            cursor.execute('''
                UPDATE leaderboard SET
                    score = ?, performance_score = ?, efficiency_score = ?, carbon_score = ?,
                    latency_ms = ?, energy_joules = ?, carbon_gco2e = ?,
                    accuracy = ?, throughput_tokens_per_s = ?,
                    is_public = ?, evaluation_id = ?, metadata_json = ?,
                    submitted_at = CURRENT_TIMESTAMP
                WHERE model_name = ? AND task_name = ?
            ''', (
                score, performance_score, efficiency_score, carbon_score,
                latency_ms, energy_joules, carbon_gco2e,
                accuracy, throughput,
                1 if make_public else 0,
                evaluation_id,
                json.dumps(metadata, ensure_ascii=False),
                model_name,
                task_name,
            ))
            conn.commit()
            
            rank_info = self._calculate_rank(model_name, task_name, score)
            
            return {
                "leaderboard_url": f"https://benchmark.dflca.ai/leaderboard",
                "model_url": f"https://benchmark.dflca.ai/models/{model_name}",
                "rank": rank_info["rank"],
                "total_entries": rank_info["total"],
                "percentile": rank_info["percentile"],
                "is_public": make_public,
                "updated": True,
            }
        finally:
            conn.close()
    
    def _calculate_overall_score(self, metrics: Dict[str, Any]) -> float:
        """
        计算综合得分
        
        Args:
            metrics: 指标字典
        
        Returns:
            综合得分（0-100）
        """
        score = 0.0
        
        # 性能得分（0-40分）
        performance = metrics.get("performance", {})
        if performance.get("accuracy"):
            score += performance["accuracy"] * 40
        if performance.get("latency_ms"):
            latency = performance["latency_ms"]
            if latency < 100:
                score += 20
            elif latency < 500:
                score += 15
            elif latency < 1000:
                score += 10
            else:
                score += 5
        
        # 能效得分（0-30分）
        efficiency = metrics.get("efficiency", {})
        cpu_usage = efficiency.get("cpu_usage", 100)
        if cpu_usage < 30:
            score += 30
        elif cpu_usage < 50:
            score += 25
        elif cpu_usage < 70:
            score += 20
        else:
            score += 10
        
        # 碳排放得分（0-30分）
        carbon = metrics.get("carbon", {})
        carbon_g = carbon.get("carbon_footprint_g", 999)
        if carbon_g < 0.001:
            score += 30
        elif carbon_g < 0.01:
            score += 25
        elif carbon_g < 0.1:
            score += 20
        else:
            score += 10
        
        return min(100, score)
    
    def _calculate_rank(self, model_name: str, task_name: str, score: float) -> Dict[str, Any]:
        """
        计算排名和百分位数
        
        Args:
            model_name: 模型名称
            task_name: 任务名称
            score: 得分
        
        Returns:
            包含排名、总数、百分位数的字典
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取所有公开的、相同任务的记录，按得分降序排列
        cursor.execute('''
            SELECT model_name, score 
            FROM leaderboard 
            WHERE is_public = 1 AND task_name = ?
            ORDER BY score DESC
        ''', (task_name,))
        
        entries = cursor.fetchall()
        conn.close()
        
        if not entries:
            return {
                "rank": 1,
                "total": 0,
                "percentile": 100,
            }
        
        # 找到当前模型的排名
        rank = 1
        for entry_model, entry_score in entries:
            if entry_model == model_name and abs(entry_score - score) < 0.01:
                break
            if entry_score > score:
                rank += 1
        
        total = len(entries)
        percentile = ((total - rank + 1) / total * 100) if total > 0 else 100
        
        return {
            "rank": rank,
            "total": total,
            "percentile": round(percentile, 2),
        }
    
    def get_leaderboard(
        self,
        task_name: Optional[str] = None,
        limit: int = 100,
        include_private: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        获取排行榜
        
        Args:
            task_name: 可选的任务名称过滤
            limit: 返回结果数量限制
            include_private: 是否包含私有记录
        
        Returns:
            排行榜条目列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if task_name:
            if include_private:
                cursor.execute('''
                    SELECT * FROM leaderboard 
                    WHERE task_name = ?
                    ORDER BY score DESC, submitted_at DESC
                    LIMIT ?
                ''', (task_name, limit))
            else:
                cursor.execute('''
                    SELECT * FROM leaderboard 
                    WHERE task_name = ? AND is_public = 1
                    ORDER BY score DESC, submitted_at DESC
                    LIMIT ?
                ''', (task_name, limit))
        else:
            if include_private:
                cursor.execute('''
                    SELECT * FROM leaderboard 
                    ORDER BY score DESC, submitted_at DESC
                    LIMIT ?
                ''', (limit,))
            else:
                cursor.execute('''
                    SELECT * FROM leaderboard 
                    WHERE is_public = 1
                    ORDER BY score DESC, submitted_at DESC
                    LIMIT ?
                ''', (limit,))
        
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        
        leaderboard = []
        for i, row in enumerate(rows, 1):
            entry = dict(zip(columns, row))
            entry["rank"] = i
            if entry.get("metadata_json"):
                entry["metadata"] = json.loads(entry["metadata_json"])
            leaderboard.append(entry)
        
        return leaderboard
    
    def get_model_stats(self, model_name: str) -> Dict[str, Any]:
        """
        获取模型的统计信息
        
        Args:
            model_name: 模型名称
        
        Returns:
            模型统计信息
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_submissions,
                AVG(score) as avg_score,
                MAX(score) as best_score,
                MIN(score) as worst_score,
                COUNT(DISTINCT task_name) as tasks_count
            FROM leaderboard
            WHERE model_name = ? AND is_public = 1
        ''', (model_name,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row or row[0] == 0:
            return {
                "model_name": model_name,
                "total_submissions": 0,
                "avg_score": None,
                "best_score": None,
                "worst_score": None,
                "tasks_count": 0,
            }
        
        return {
            "model_name": model_name,
            "total_submissions": row[0],
            "avg_score": round(row[1], 2) if row[1] else None,
            "best_score": round(row[2], 2) if row[2] else None,
            "worst_score": round(row[3], 2) if row[3] else None,
            "tasks_count": row[4],
        }
    
    def submit_to_public_leaderboard(self, results: Dict[str, Any]):
        """
        提交到公开排行榜（内部方法）
        
        Args:
            results: 评测结果
        """
        self.publish_results(results, make_public=True)


# 全局实例
leaderboard = Leaderboard()

"""测试评测API - 完整的测试脚本"""
import requests
import json
import time
from typing import Dict, Any, Optional


# API 基础URL
BASE_URL = "http://localhost:8000"


def test_health_check() -> bool:
    """测试健康检查端点"""
    print("=" * 60)
    print("测试 1: 健康检查")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ 健康检查通过")
        print(f"   状态: {result.get('status')}")
        print(f"   数据库: {result.get('database')}")
        print(f"   评测器: {result.get('evaluator')}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ 健康检查失败: {e}")
        return False


def test_evaluate(
    model_name: str = "test-model",
    tasks: list = None,
    model_endpoint: str = "http://localhost:5000/generate"
) -> Optional[Dict[str, Any]]:
    """
    测试评测API
    
    Args:
        model_name: 模型名称
        tasks: 评测任务列表
        model_endpoint: 模型API端点
    
    Returns:
        评测结果字典，如果失败则返回 None
    """
    if tasks is None:
        tasks = ["MMLU", "GSM8K"]
    
    print("\n" + "=" * 60)
    print("测试 2: 评测API")
    print("=" * 60)
    
    test_request = {
        "model_name": model_name,
        "tasks": tasks,
        "model_endpoint": model_endpoint
    }
    
    print(f"请求内容:")
    print(json.dumps(test_request, indent=2, ensure_ascii=False))
    print(f"\n发送请求到: {BASE_URL}/evaluate")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/evaluate",
            json=test_request,
            timeout=300  # 5分钟超时，因为评测可能需要较长时间
        )
        elapsed_time = time.time() - start_time
        
        response.raise_for_status()
        result = response.json()
        
        print(f"\n✅ 评测成功 (耗时: {elapsed_time:.2f}秒)")
        print(f"   状态: {result.get('status')}")
        print(f"   模型: {result.get('model')}")
        print(f"   评测ID: {result.get('evaluation_id')}")
        
        # 显示指标摘要
        metrics = result.get('metrics', {})
        if metrics:
            print(f"\n   指标摘要:")
            perf = metrics.get('performance', {})
            if perf:
                print(f"     准确率: {perf.get('accuracy', 'N/A')}")
                print(f"     延迟: {perf.get('latency_ms', 'N/A')} ms")
            
            eff = metrics.get('efficiency', {})
            if eff:
                print(f"     CPU使用率: {eff.get('cpu_usage', 'N/A')}%")
                print(f"     内存使用率: {eff.get('memory_usage', 'N/A')}%")
            
            carbon = metrics.get('carbon', {})
            if carbon:
                print(f"     碳排放: {carbon.get('carbon_footprint_g', 'N/A')} gCO2e")
        
        return result
    except requests.exceptions.Timeout:
        print(f"\n❌ 评测超时（超过5分钟）")
        return None
    except requests.exceptions.RequestException as e:
        print(f"\n❌ 评测失败: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"   错误详情: {json.dumps(error_detail, indent=2, ensure_ascii=False)}")
            except:
                print(f"   响应内容: {e.response.text}")
        return None


def test_get_results(model_name: str = "test-model") -> bool:
    """测试获取评测结果"""
    print("\n" + "=" * 60)
    print("测试 3: 获取评测结果")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/results/{model_name}", timeout=10)
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ 获取结果成功")
        print(f"   模型: {result.get('model')}")
        print(f"   历史记录数: {len(result.get('history', []))}")
        
        if result.get('history'):
            print(f"\n   最近一次评测:")
            latest = result['history'][0]
            print(f"     ID: {latest.get('id')}")
            print(f"     时间: {latest.get('timestamp')}")
        
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ 获取结果失败: {e}")
        return False


def test_get_all_results() -> bool:
    """测试获取所有评测结果"""
    print("\n" + "=" * 60)
    print("测试 4: 获取所有评测结果")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/results", timeout=10)
        response.raise_for_status()
        
        results = response.json()
        print(f"✅ 获取所有结果成功")
        print(f"   总记录数: {len(results)}")
        
        if results:
            print(f"\n   前5条记录:")
            for i, r in enumerate(results[:5], 1):
                print(f"     {i}. ID: {r.get('id')}, 模型: {r.get('model_name')}, 时间: {r.get('timestamp')}")
        
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ 获取所有结果失败: {e}")
        return False


def test_list_models() -> bool:
    """测试列出所有模型"""
    print("\n" + "=" * 60)
    print("测试 5: 列出所有模型")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/models", timeout=10)
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ 列出模型成功")
        print(f"   模型数量: {result.get('count')}")
        print(f"   模型列表: {', '.join(result.get('models', []))}")
        
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ 列出模型失败: {e}")
        return False


def test_invalid_request() -> bool:
    """测试无效请求（错误处理）"""
    print("\n" + "=" * 60)
    print("测试 6: 无效请求（错误处理）")
    print("=" * 60)
    
    # 测试缺少必需字段
    invalid_request = {
        "model_name": "test-model"
        # 缺少 tasks 和 model_endpoint
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/evaluate",
            json=invalid_request,
            timeout=10
        )
        
        if response.status_code == 422:
            print(f"✅ 错误处理正确（返回422状态码）")
            error_detail = response.json()
            print(f"   错误详情: {json.dumps(error_detail, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"⚠️  预期422状态码，但收到: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")
        return False


def test_nonexistent_model() -> bool:
    """测试不存在的模型"""
    print("\n" + "=" * 60)
    print("测试 7: 查询不存在的模型")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/results/nonexistent-model-12345", timeout=10)
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ 查询成功（返回空历史）")
        print(f"   模型: {result.get('model')}")
        print(f"   历史记录数: {len(result.get('history', []))}")
        
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ 查询失败: {e}")
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("DF-LCA AI Benchmark API 测试套件")
    print("=" * 60)
    print(f"\nAPI 地址: {BASE_URL}")
    print("注意: 确保 API 服务正在运行")
    print("启动命令: uvicorn simple_api:app --host 0.0.0.0 --port 8000")
    print("=" * 60)
    
    # 测试结果统计
    results = {
        "passed": 0,
        "failed": 0,
        "total": 0
    }
    
    # 运行测试
    tests = [
        ("健康检查", test_health_check),
        ("评测API", lambda: test_evaluate() is not None),
        ("获取评测结果", lambda: test_get_results("test-model")),
        ("获取所有结果", test_get_all_results),
        ("列出所有模型", test_list_models),
        ("无效请求处理", test_invalid_request),
        ("查询不存在模型", test_nonexistent_model),
    ]
    
    for test_name, test_func in tests:
        results["total"] += 1
        try:
            if test_func():
                results["passed"] += 1
            else:
                results["failed"] += 1
        except Exception as e:
            print(f"\n❌ 测试 '{test_name}' 发生异常: {e}")
            results["failed"] += 1
    
    # 显示测试总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"总测试数: {results['total']}")
    print(f"通过: {results['passed']} ✅")
    print(f"失败: {results['failed']} ❌")
    print(f"成功率: {results['passed']/results['total']*100:.1f}%")
    print("=" * 60)
    
    if results["failed"] == 0:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  有 {results['failed']} 个测试失败")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

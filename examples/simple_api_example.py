"""Example: Using the Simple API for model evaluation."""
import requests
import json

# API 基础URL
BASE_URL = "http://localhost:8000"


def test_evaluate():
    """测试评测端点"""
    url = f"{BASE_URL}/evaluate"
    
    # 评测请求
    payload = {
        "model_name": "GPT-4",
        "tasks": ["MMLU", "GSM8K"],
        "model_endpoint": "http://localhost:8000/v1/completions"  # 示例端点
    }
    
    print("发送评测请求...")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    print("-" * 60)
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        print("\n✅ 评测成功!")
        print(f"状态: {result['status']}")
        print(f"模型: {result['model']}")
        print(f"评测ID: {result.get('evaluation_id')}")
        print("\n指标:")
        print(json.dumps(result['metrics'], indent=2, ensure_ascii=False))
        
        return result
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"响应内容: {e.response.text}")
        return None


def test_get_results(model_name: str = "GPT-4"):
    """测试获取结果端点"""
    url = f"{BASE_URL}/results/{model_name}"
    
    print(f"\n获取模型 '{model_name}' 的历史结果...")
    print(f"URL: {url}")
    print("-" * 60)
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        print(f"\n✅ 获取成功!")
        print(f"模型: {result['model']}")
        print(f"历史记录数: {len(result['history'])}")
        
        if result['history']:
            print("\n最近一次评测:")
            latest = result['history'][0]
            print(f"  ID: {latest['id']}")
            print(f"  时间: {latest['timestamp']}")
            print(f"  指标: {json.dumps(latest['metrics'], indent=4, ensure_ascii=False)}")
        
        return result
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"响应内容: {e.response.text}")
        return None


def test_list_models():
    """测试列出所有模型"""
    url = f"{BASE_URL}/models"
    
    print("\n获取所有已评测的模型...")
    print(f"URL: {url}")
    print("-" * 60)
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        print(f"\n✅ 获取成功!")
        print(f"模型数量: {result['count']}")
        print(f"模型列表: {', '.join(result['models'])}")
        
        return result
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"响应内容: {e.response.text}")
        return None


def test_health():
    """测试健康检查端点"""
    url = f"{BASE_URL}/health"
    
    print("检查API健康状态...")
    print(f"URL: {url}")
    print("-" * 60)
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        
        result = response.json()
        print(f"\n✅ API健康!")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        return result
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")
        return None


def main():
    """主函数"""
    print("=" * 60)
    print("Simple API 使用示例")
    print("=" * 60)
    print("\n注意: 确保 Simple API 服务正在运行:")
    print("  uvicorn simple_api:app --host 0.0.0.0 --port 8000")
    print("=" * 60)
    
    # 健康检查
    health = test_health()
    if not health:
        print("\n⚠️  API服务可能未启动，请先启动服务")
        return
    
    # 执行评测
    eval_result = test_evaluate()
    
    # 获取结果
    if eval_result:
        test_get_results(eval_result['model'])
    
    # 列出所有模型
    test_list_models()


if __name__ == "__main__":
    main()

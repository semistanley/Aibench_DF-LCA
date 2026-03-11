"""简单测试脚本 - 快速测试评测API"""
import requests
import json

# API 基础URL
BASE_URL = "http://localhost:8000"

# 测试评测API
test_request = {
    "model_name": "test-model",
    "tasks": ["MMLU", "GSM8K"],
    "model_endpoint": "http://localhost:5000/generate"  # 替换为实际模型端点
}

print("发送评测请求...")
print(f"URL: {BASE_URL}/evaluate")
print(f"请求内容: {json.dumps(test_request, indent=2, ensure_ascii=False)}")
print("-" * 60)

try:
    response = requests.post(
        f"{BASE_URL}/evaluate",
        json=test_request,
        timeout=300  # 5分钟超时
    )
    
    response.raise_for_status()
    result = response.json()
    
    print("\n✅ 评测成功!")
    print("评测结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
except requests.exceptions.ConnectionError:
    print("\n❌ 连接失败: 请确保 API 服务正在运行")
    print("启动命令: uvicorn simple_api:app --host 0.0.0.0 --port 8000")
except requests.exceptions.Timeout:
    print("\n❌ 请求超时: 评测时间超过5分钟")
except requests.exceptions.RequestException as e:
    print(f"\n❌ 请求失败: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"响应状态码: {e.response.status_code}")
        print(f"响应内容: {e.response.text}")

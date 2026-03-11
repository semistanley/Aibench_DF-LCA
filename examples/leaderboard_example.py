"""Example: Using the Leaderboard system."""
import requests
import json

BASE_URL = "http://localhost:8000"


def example_publish_to_leaderboard():
    """示例：执行评测并自动发布到排行榜"""
    print("=" * 60)
    print("示例 1: 执行评测并自动发布到排行榜")
    print("=" * 60)
    
    # 执行评测（自动发布到排行榜）
    response = requests.post(
        f"{BASE_URL}/evaluate",
        params={"publish_to_leaderboard": True},
        json={
            "model_name": "example-model",
            "tasks": ["MMLU", "GSM8K"],
            "model_endpoint": "http://localhost:5000/generate"  # 示例端点
        },
        timeout=300
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ 评测成功并已发布到排行榜")
        print(f"   模型: {result['model']}")
        print(f"   评测ID: {result.get('evaluation_id')}")
        
        if result.get("leaderboard"):
            lb = result["leaderboard"]
            print(f"\n   排行榜信息:")
            print(f"   排名: {lb.get('rank')}")
            print(f"   总条目: {lb.get('total_entries')}")
            print(f"   百分位数: {lb.get('percentile')}%")
            print(f"   排行榜URL: {lb.get('leaderboard_url')}")
            print(f"   模型URL: {lb.get('model_url')}")
    else:
        print(f"❌ 评测失败: {response.status_code}")
        print(response.text)


def example_get_leaderboard():
    """示例：获取排行榜"""
    print("\n" + "=" * 60)
    print("示例 2: 获取排行榜")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/leaderboard?limit=10")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 获取排行榜成功")
        print(f"   总条目: {result.get('total')}")
        print(f"\n   前10名:")
        
        for entry in result.get("entries", [])[:10]:
            print(f"   {entry.get('rank')}. {entry.get('model_name')}: {entry.get('score', 0):.2f}分")
    else:
        print(f"❌ 获取失败: {response.status_code}")


def example_get_model_stats():
    """示例：获取模型统计信息"""
    print("\n" + "=" * 60)
    print("示例 3: 获取模型统计信息")
    print("=" * 60)
    
    model_name = "example-model"
    response = requests.get(f"{BASE_URL}/leaderboard/models/{model_name}")
    
    if response.status_code == 200:
        stats = response.json()
        print(f"✅ 获取模型统计成功")
        print(f"   模型: {stats.get('model_name')}")
        print(f"   总提交数: {stats.get('total_submissions')}")
        print(f"   平均得分: {stats.get('avg_score')}")
        print(f"   最佳得分: {stats.get('best_score')}")
        print(f"   最差得分: {stats.get('worst_score')}")
        print(f"   任务数量: {stats.get('tasks_count')}")
    else:
        print(f"❌ 获取失败: {response.status_code}")


def example_manual_publish():
    """示例：手动发布评测结果"""
    print("\n" + "=" * 60)
    print("示例 4: 手动发布评测结果到排行榜")
    print("=" * 60)
    
    evaluation_id = 1  # 替换为实际的评测ID
    
    response = requests.post(
        f"{BASE_URL}/leaderboard/publish",
        params={
            "evaluation_id": evaluation_id,
            "make_public": True
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ 发布成功")
        print(f"   排名: {result.get('rank')}")
        print(f"   百分位数: {result.get('percentile')}%")
        print(f"   排行榜URL: {result.get('leaderboard_url')}")
    else:
        print(f"❌ 发布失败: {response.status_code}")
        print(response.text)


def main():
    """主函数"""
    print("=" * 60)
    print("排行榜系统使用示例")
    print("=" * 60)
    print(f"\nAPI 地址: {BASE_URL}")
    print("注意: 确保 API 服务正在运行")
    print("=" * 60)
    
    try:
        # 示例 1: 执行评测并自动发布
        example_publish_to_leaderboard()
        
        # 示例 2: 获取排行榜
        example_get_leaderboard()
        
        # 示例 3: 获取模型统计
        example_get_model_stats()
        
        # 示例 4: 手动发布
        # example_manual_publish()
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 连接失败: 请确保 API 服务正在运行")
        print("启动命令: uvicorn simple_api:app --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

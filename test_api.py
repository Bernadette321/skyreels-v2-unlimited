#!/usr/bin/env python3
"""
SkyReels V2 API 测试脚本
用于验证Docker容器中的API是否正常工作
"""

import requests
import json
import time
import sys

# API基础URL
BASE_URL = "http://localhost:8000"

def test_health():
    """测试健康检查端点"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_model_info():
    """测试模型信息端点"""
    print("\n📋 Testing model info endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/models/info", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Model info: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"❌ Model info failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Model info error: {e}")
        return False

def test_video_generation():
    """测试视频生成（使用短视频测试）"""
    print("\n🎬 Testing video generation...")
    
    # 使用较短的视频进行测试
    payload = {
        "prompt": "A beautiful sunset over the ocean with gentle waves, golden light reflecting on water, peaceful and serene atmosphere",
        "duration": 30,  # 30秒测试视频
        "resolution": "720p"
    }
    
    try:
        # 发起生成请求
        print("📤 Sending generation request...")
        response = requests.post(
            f"{BASE_URL}/generate",
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Generation request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        task_id = data.get("task_id")
        print(f"✅ Generation started, task ID: {task_id}")
        print(f"📊 Estimated duration: {data.get('estimated_duration_minutes', 'unknown')} minutes")
        
        # 轮询状态
        print("\n⏳ Monitoring generation progress...")
        max_wait = 600  # 最大等待10分钟
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                status_response = requests.get(f"{BASE_URL}/status/{task_id}", timeout=10)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data.get("status")
                    progress = status_data.get("progress", 0)
                    elapsed = status_data.get("elapsed_time", 0)
                    
                    print(f"📈 Status: {status}, Progress: {progress:.1%}, Elapsed: {elapsed:.1f}s")
                    
                    if status == "completed":
                        print(f"🎉 Video generation completed!")
                        print(f"📁 Video path: {status_data.get('video_path')}")
                        
                        # 测试下载
                        download_response = requests.get(f"{BASE_URL}/download/{task_id}", timeout=30)
                        if download_response.status_code == 200:
                            print("✅ Video download test passed")
                        else:
                            print(f"⚠️  Video download test failed: {download_response.status_code}")
                        
                        return True
                    
                    elif status == "failed":
                        print(f"❌ Video generation failed: {status_data.get('error_message')}")
                        return False
                    
                    elif status in ["generating", "downloading_model", "initialized"]:
                        time.sleep(10)  # 等待10秒后再次检查
                        continue
                    
                else:
                    print(f"❌ Status check failed: {status_response.status_code}")
                    return False
                    
            except Exception as e:
                print(f"⚠️  Status check error: {e}")
                time.sleep(5)
                continue
        
        print("⏰ Test timeout reached")
        return False
        
    except Exception as e:
        print(f"❌ Generation test error: {e}")
        return False

def test_tasks_endpoint():
    """测试任务列表端点"""
    print("\n📝 Testing tasks endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/tasks", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Tasks endpoint working, found {len(data.get('tasks', []))} tasks")
            return True
        else:
            print(f"❌ Tasks endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Tasks endpoint error: {e}")
        return False

def main():
    """运行所有测试"""
    print("🧪 SkyReels V2 API Testing Suite")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health),
        ("Model Info", test_model_info),
        ("Tasks Endpoint", test_tasks_endpoint),
    ]
    
    # 运行基础测试
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        if test_func():
            passed += 1
        time.sleep(1)  # 短暂暂停
    
    print(f"\n📊 Basic Tests Results: {passed}/{total} passed")
    
    # 询问是否运行视频生成测试
    if passed == total:
        print("\n🎬 Video generation test is optional and may take several minutes.")
        response = input("Do you want to run video generation test? (y/N): ").strip().lower()
        
        if response in ['y', 'yes']:
            if test_video_generation():
                passed += 1
            total += 1
    
    # 最终结果
    print("\n" + "=" * 50)
    if passed == total:
        print("🎉 All tests passed! SkyReels V2 API is working correctly.")
        sys.exit(0)
    else:
        print(f"❌ {total - passed} test(s) failed. Please check the logs.")
        sys.exit(1)

if __name__ == "__main__":
    main() 
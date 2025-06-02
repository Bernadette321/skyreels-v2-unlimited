#!/usr/bin/env python3
"""
SkyReels V2 Unlimited API 测试脚本
测试无限制长视频生成功能
"""

import time
import json
import requests
from datetime import datetime
from typing import Dict, List

# 配置
API_BASE_URL = "http://localhost:8000"
TEST_PROMPTS = [
    {
        "name": "短视频测试",
        "prompt": "A beautiful sunrise over mountains with birds flying",
        "resolution": "720p",
        "duration": 30,
        "quality": "high"
    },
    {
        "name": "中等视频测试", 
        "prompt": "A cinematic journey through a magical forest with changing seasons",
        "resolution": "1080p",
        "duration": 300,  # 5分钟
        "quality": "high"
    },
    {
        "name": "长视频测试",
        "prompt": "An epic space adventure showing planets, stars, and cosmic phenomena",
        "resolution": "1080p", 
        "duration": 1800,  # 30分钟
        "quality": "ultra"
    },
    {
        "name": "超长视频测试",
        "prompt": "A complete day cycle in a bustling city from sunrise to sunset",
        "resolution": "1080p",
        "duration": 3600,  # 60分钟
        "quality": "ultra",
        "enable_audio": True
    }
]

class SkyReelsUnlimitedTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
    
    def test_health_check(self) -> bool:
        """测试健康检查端点"""
        print("🔍 测试健康检查...")
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 服务健康: {data.get('status')}")
                print(f"📊 GPU信息: {data.get('gpu_info', {}).get('name')}")
                print(f"💾 GPU内存: {data.get('gpu_info', {}).get('memory'):.1f}GB")
                print(f"⚡ 能力等级: {data.get('gpu_info', {}).get('capability')}")
                return True
            else:
                print(f"❌ 健康检查失败: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 健康检查错误: {e}")
            return False
    
    def test_model_info(self) -> bool:
        """测试模型信息端点"""
        print("\n📋 测试模型信息...")
        try:
            response = self.session.get(f"{self.base_url}/models/info", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 模型名称: {data.get('model_name')}")
                print(f"🎬 支持分辨率: {', '.join(data.get('supported_resolutions', []))}")
                print(f"⏱️  最大时长: {data.get('max_duration')}秒")
                print(f"🚀 功能特性:")
                for feature in data.get('features', []):
                    print(f"   • {feature}")
                return True
            else:
                print(f"❌ 模型信息获取失败: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 模型信息错误: {e}")
            return False
    
    def test_system_stats(self) -> bool:
        """测试系统统计端点"""
        print("\n📈 测试系统统计...")
        try:
            response = self.session.get(f"{self.base_url}/system/stats", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 系统统计获取成功")
                
                # GPU信息
                gpu_info = data.get('gpu', {})
                if gpu_info.get('total_gpus', 0) > 0:
                    print(f"🎮 GPU状态:")
                    for gpu in gpu_info.get('gpus', []):
                        print(f"   GPU {gpu['gpu_id']}: {gpu['name']}")
                        print(f"   内存: {gpu['allocated']:.1f}GB / {gpu['total']:.1f}GB")
                
                # 系统内存
                sys_mem = data.get('system_memory', {})
                print(f"💾 系统内存: {sys_mem.get('used', 0):.1f}GB / {sys_mem.get('total', 0):.1f}GB")
                
                # 磁盘使用
                disk = data.get('disk', {})
                print(f"💿 磁盘使用: {disk.get('used', 0):.1f}GB / {disk.get('total', 0):.1f}GB")
                
                return True
            else:
                print(f"❌ 系统统计获取失败: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 系统统计错误: {e}")
            return False
    
    def start_video_generation(self, test_config: Dict) -> str:
        """启动视频生成任务"""
        print(f"\n🎬 开始测试: {test_config['name']}")
        print(f"📋 参数: {test_config['resolution']} {test_config['duration']}秒")
        print(f"🎯 提示词: {test_config['prompt'][:50]}...")
        
        try:
            response = self.session.post(
                f"{self.base_url}/generate",
                json=test_config,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                task_id = data.get('task_id')
                estimated_time = data.get('estimated_duration_minutes', 0)
                
                print(f"✅ 任务已创建: {task_id}")
                print(f"⏱️  预计时间: {estimated_time}分钟")
                
                # 显示警告（如果有）
                warnings = data.get('warnings', [])
                for warning in warnings:
                    print(f"⚠️  警告: {warning}")
                
                return task_id
            else:
                print(f"❌ 任务创建失败: HTTP {response.status_code}")
                print(f"错误: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ 任务创建错误: {e}")
            return None
    
    def monitor_task_progress(self, task_id: str, timeout_minutes: int = 60) -> bool:
        """监控任务进度"""
        if not task_id:
            return False
            
        print(f"📊 监控任务进度: {task_id}")
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        
        while time.time() - start_time < timeout_seconds:
            try:
                response = self.session.get(f"{self.base_url}/tasks/{task_id}/status")
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status')
                    progress = data.get('progress', 0)
                    
                    print(f"\r📈 状态: {status} | 进度: {progress*100:.1f}%", end='', flush=True)
                    
                    if status == 'completed':
                        print(f"\n✅ 任务完成!")
                        result_path = data.get('result_path')
                        if result_path:
                            print(f"📁 结果文件: {result_path}")
                        return True
                    elif status == 'failed':
                        print(f"\n❌ 任务失败!")
                        error = data.get('error')
                        if error:
                            print(f"错误信息: {error}")
                        return False
                    elif status == 'cancelled':
                        print(f"\n⏹️  任务已取消")
                        return False
                    
                    time.sleep(10)  # 每10秒检查一次
                else:
                    print(f"\n❌ 状态查询失败: HTTP {response.status_code}")
                    return False
                    
            except Exception as e:
                print(f"\n❌ 监控错误: {e}")
                return False
        
        print(f"\n⏰ 任务超时 ({timeout_minutes}分钟)")
        return False
    
    def test_video_generation(self, test_config: Dict, timeout_minutes: int = 60) -> Dict:
        """测试视频生成"""
        start_time = time.time()
        
        # 启动任务
        task_id = self.start_video_generation(test_config)
        if not task_id:
            return {
                'test_name': test_config['name'],
                'success': False,
                'error': '任务创建失败',
                'duration': 0
            }
        
        # 监控进度
        success = self.monitor_task_progress(task_id, timeout_minutes)
        
        end_time = time.time()
        duration = end_time - start_time
        
        result = {
            'test_name': test_config['name'],
            'task_id': task_id,
            'success': success,
            'duration': duration,
            'video_duration': test_config['duration'],
            'resolution': test_config['resolution'],
            'generation_ratio': duration / test_config['duration'] if test_config['duration'] > 0 else 0
        }
        
        return result
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始SkyReels V2无限制版API测试")
        print("=" * 50)
        
        # 基础测试
        if not self.test_health_check():
            print("❌ 健康检查失败，终止测试")
            return
        
        if not self.test_model_info():
            print("❌ 模型信息测试失败")
        
        if not self.test_system_stats():
            print("❌ 系统统计测试失败")
        
        # 视频生成测试
        print(f"\n🎬 开始视频生成测试 ({len(TEST_PROMPTS)}个测试)")
        print("=" * 50)
        
        for i, test_config in enumerate(TEST_PROMPTS, 1):
            print(f"\n【测试 {i}/{len(TEST_PROMPTS)}】")
            
            # 根据视频时长设置超时
            timeout_minutes = max(60, test_config['duration'] // 30)  # 至少60分钟
            
            result = self.test_video_generation(test_config, timeout_minutes)
            self.test_results.append(result)
            
            if result['success']:
                print(f"✅ 测试成功!")
                print(f"⏱️  生成时间: {result['duration']:.1f}秒")
                print(f"📊 效率比: {result['generation_ratio']:.2f} (生成时间/视频时长)")
            else:
                print(f"❌ 测试失败: {result.get('error', '未知错误')}")
        
        # 输出测试报告
        self.generate_test_report()
    
    def generate_test_report(self):
        """生成测试报告"""
        print("\n📋 测试报告")
        print("=" * 50)
        
        successful_tests = [r for r in self.test_results if r['success']]
        failed_tests = [r for r in self.test_results if not r['success']]
        
        print(f"📊 总测试数: {len(self.test_results)}")
        print(f"✅ 成功: {len(successful_tests)}")
        print(f"❌ 失败: {len(failed_tests)}")
        print(f"📈 成功率: {len(successful_tests)/len(self.test_results)*100:.1f}%")
        
        if successful_tests:
            print(f"\n🎯 成功测试详情:")
            for result in successful_tests:
                print(f"  • {result['test_name']}")
                print(f"    分辨率: {result['resolution']}")
                print(f"    视频时长: {result['video_duration']}秒")
                print(f"    生成时间: {result['duration']:.1f}秒")
                print(f"    效率比: {result['generation_ratio']:.2f}")
                print()
        
        if failed_tests:
            print(f"❌ 失败测试:")
            for result in failed_tests:
                print(f"  • {result['test_name']}: {result.get('error', '未知错误')}")
        
        # 保存测试报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"test_report_unlimited_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total_tests': len(self.test_results),
                    'successful': len(successful_tests),
                    'failed': len(failed_tests),
                    'success_rate': len(successful_tests)/len(self.test_results)*100
                },
                'results': self.test_results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"📄 详细报告已保存至: {report_file}")

def main():
    """主函数"""
    print("🎬 SkyReels V2 Unlimited API Tester")
    print("测试无限制长视频生成功能")
    print()
    
    tester = SkyReelsUnlimitedTester(API_BASE_URL)
    tester.run_all_tests()

if __name__ == "__main__":
    main() 
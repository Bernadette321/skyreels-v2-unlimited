#!/usr/bin/env python3
"""
SkyReels V2 模型下载脚本
自动下载和验证SkyReels-V2所需的模型文件
"""

import os
import sys
from pathlib import Path
from huggingface_hub import snapshot_download, hf_hub_download
import json

def check_disk_space():
    """检查磁盘空间"""
    import shutil
    total, used, free = shutil.disk_usage("/app")
    free_gb = free // (1024**3)
    print(f"💾 可用磁盘空间: {free_gb}GB")
    
    if free_gb < 50:
        print("⚠️  警告: 磁盘空间不足50GB，可能无法下载所有模型")
        return False
    return True

def download_skyreels_models():
    """下载SkyReels-V2模型"""
    models = {
        'SkyReels-V2-DF-14B-720P': {
            'repo_id': 'Skywork/SkyReels-V2-DF-14B-720P',
            'local_dir': '/app/models/SkyReels-V2-DF-14B-720P',
            'description': 'Diffusion Forcing 720P 模型'
        },
        'SkyReels-V2-I2V-14B-720P': {
            'repo_id': 'Skywork/SkyReels-V2-I2V-14B-720P', 
            'local_dir': '/app/models/SkyReels-V2-I2V-14B-720P',
            'description': 'Image-to-Video 720P 模型'
        }
    }
    
    print("🤖 开始下载SkyReels-V2模型...")
    
    for model_name, config in models.items():
        local_dir = Path(config['local_dir'])
        
        if local_dir.exists() and any(local_dir.iterdir()):
            print(f"✅ 模型已存在: {model_name}")
            continue
            
        print(f"📥 下载模型: {model_name} ({config['description']})")
        print(f"🎯 目标目录: {config['local_dir']}")
        
        try:
            # 创建目录
            local_dir.mkdir(parents=True, exist_ok=True)
            
            # 下载模型
            snapshot_download(
                repo_id=config['repo_id'],
                local_dir=config['local_dir'],
                local_dir_use_symlinks=False,
                resume_download=True
            )
            
            print(f"✅ 模型下载完成: {model_name}")
            
            # 验证下载
            if verify_model_download(config['local_dir']):
                print(f"✅ 模型验证通过: {model_name}")
            else:
                print(f"❌ 模型验证失败: {model_name}")
                
        except Exception as e:
            print(f"❌ 模型下载失败 {model_name}: {e}")
            # 如果下载失败，尝试下载最小必需文件
            try_download_essential_files(config)

def try_download_essential_files(config):
    """尝试下载核心文件"""
    essential_files = [
        "config.json",
        "model.safetensors", 
        "tokenizer.json",
        "tokenizer_config.json"
    ]
    
    print(f"🔄 尝试下载核心文件...")
    local_dir = Path(config['local_dir'])
    local_dir.mkdir(parents=True, exist_ok=True)
    
    for filename in essential_files:
        try:
            hf_hub_download(
                repo_id=config['repo_id'],
                filename=filename,
                local_dir=config['local_dir'],
                local_dir_use_symlinks=False
            )
            print(f"✅ 下载核心文件: {filename}")
        except Exception as e:
            print(f"⚠️  跳过文件 {filename}: {e}")

def verify_model_download(model_dir):
    """验证模型下载完整性"""
    model_path = Path(model_dir)
    if not model_path.exists():
        return False
    
    # 检查必需文件
    required_files = ["config.json"]
    for required_file in required_files:
        if not (model_path / required_file).exists():
            print(f"❌ 缺少必需文件: {required_file}")
            return False
    
    # 检查模型文件
    model_files = list(model_path.glob("*.safetensors")) + list(model_path.glob("*.bin"))
    if not model_files:
        print(f"❌ 未找到模型权重文件")
        return False
    
    return True

def setup_model_config():
    """设置模型配置"""
    config_dir = Path("/app/config")
    config_dir.mkdir(exist_ok=True)
    
    # 创建模型映射配置
    model_config = {
        "models": {
            "df_model": "/app/models/SkyReels-V2-DF-14B-720P",
            "i2v_model": "/app/models/SkyReels-V2-I2V-14B-720P"
        },
        "default_settings": {
            "resolution": "720p",
            "fps": 24,
            "guidance_scale": 7.5,
            "num_inference_steps": 50
        }
    }
    
    config_file = config_dir / "models.json"
    with open(config_file, 'w') as f:
        json.dump(model_config, f, indent=2)
    
    print(f"✅ 模型配置已保存: {config_file}")

def main():
    """主函数"""
    print("🎬 SkyReels V2 模型下载器")
    print("=" * 50)
    
    # 检查磁盘空间
    if not check_disk_space():
        print("❌ 磁盘空间不足，请清理空间后重试")
        sys.exit(1)
    
    # 创建模型目录
    os.makedirs("/app/models", exist_ok=True)
    
    # 下载模型
    download_skyreels_models()
    
    # 设置配置
    setup_model_config()
    
    print("🎉 SkyReels V2 模型准备完成！")

if __name__ == "__main__":
    main() 
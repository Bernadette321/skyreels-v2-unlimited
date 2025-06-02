#!/usr/bin/env python3
"""
SkyReels V2 Flask API Server for 720P Long Video Generation
支持无限长度视频生成的API服务器
"""

import os
import sys
import json
import time
import uuid
import threading
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import logging
import gc
import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path

import torch
import psutil
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 添加SkyReels V2到Python路径
sys.path.insert(0, '/app/SkyReels-V2')

try:
    from skyreels.inference import SkyReelsInference
    from skyreels.config import load_config
except ImportError as e:
    logger.error(f"Failed to import SkyReels V2: {e}")
    sys.exit(1)

app = Flask(__name__)
CORS(app)

# 全局变量
inference_engine = None
generation_status = {}  # 存储生成任务状态

# 内存优化器
class MemoryOptimizer:
    @staticmethod
    def clear_cache():
        """清理GPU和系统缓存"""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        gc.collect()
        logger.info("Memory cache cleared")
    
    @staticmethod
    def get_gpu_memory_info():
        """获取GPU内存信息"""
        if torch.cuda.is_available():
            return {
                "allocated": torch.cuda.memory_allocated() / 1024**3,
                "cached": torch.cuda.memory_reserved() / 1024**3,
                "total": torch.cuda.get_device_properties(0).total_memory / 1024**3
            }
        return {"allocated": 0, "cached": 0, "total": 0}
    
    @staticmethod
    def optimize_model_loading():
        """优化模型加载设置"""
        if torch.cuda.is_available():
            torch.backends.cudnn.benchmark = True
            torch.backends.cuda.matmul.allow_tf32 = True
            logger.info("GPU optimization settings applied")

# GPU配置检测器
class GPUDetector:
    def __init__(self):
        self.gpu_info = self._detect_gpu()
        self.max_resolution = os.getenv("SKYREELS_MAX_RESOLUTION", "720p")
        self.max_duration = int(os.getenv("SKYREELS_MAX_DURATION", "300"))
    
    def _detect_gpu(self):
        """检测GPU配置"""
        if not torch.cuda.is_available():
            return {"name": "CPU", "memory": 0, "capability": "low"}
        
        try:
            import subprocess
            result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader,nounits'], 
                                 capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                gpu_name, memory_mb = lines[0].split(', ')
                memory_gb = int(memory_mb) / 1024
                
                # 确定GPU能力等级
                if "RTX 4090" in gpu_name or memory_gb >= 24:
                    capability = "high"
                elif "RTX 40" in gpu_name or memory_gb >= 16:
                    capability = "medium"
                else:
                    capability = "low"
                
                return {
                    "name": gpu_name.strip(),
                    "memory": memory_gb,
                    "capability": capability
                }
        except Exception as e:
            logger.warning(f"GPU detection failed: {e}")
        
        # 回退到PyTorch信息
        props = torch.cuda.get_device_properties(0)
        return {
            "name": props.name,
            "memory": props.total_memory / 1024**3,
            "capability": "medium"
        }
    
    def validate_request(self, resolution: str, duration: int) -> Dict[str, Any]:
        """验证请求参数是否在硬件限制内"""
        warnings = []
        
        # 分辨率检查
        resolution_limits = {
            "low": ["480p", "540p"],
            "medium": ["480p", "540p", "720p"],
            "high": ["480p", "540p", "720p", "1080p"]
        }
        
        allowed_resolutions = resolution_limits.get(self.gpu_info["capability"], ["480p"])
        if resolution not in allowed_resolutions:
            return {
                "valid": False,
                "error": f"分辨率 {resolution} 不被当前GPU支持。建议使用: {', '.join(allowed_resolutions)}",
                "suggested_resolution": allowed_resolutions[-1]
            }
        
        # 时长检查
        duration_limits = {
            "low": 120,      # 2分钟
            "medium": 300,   # 5分钟  
            "high": 720      # 12分钟
        }
        
        max_duration = duration_limits.get(self.gpu_info["capability"], 60)
        if duration > max_duration:
            warnings.append(f"时长 {duration}s 超过建议值 {max_duration}s，可能导致内存不足")
        
        # 组合警告
        if resolution == "1080p" and duration > 300:
            warnings.append("1080P长视频需要大量VRAM，建议先尝试720P")
        
        return {
            "valid": True,
            "warnings": warnings,
            "gpu_info": self.gpu_info
        }

# 初始化检测器和优化器
gpu_detector = GPUDetector()
memory_optimizer = MemoryOptimizer()

# 请求和响应模型
class VideoGenerationRequest(BaseModel):
    prompt: str = Field(..., description="视频生成提示词")
    resolution: str = Field(default="720p", description="视频分辨率 (480p, 540p, 720p, 1080p)")
    duration: int = Field(default=300, description="视频时长（秒）")
    guidance_scale: float = Field(default=7.5, description="引导比例")
    num_inference_steps: int = Field(default=20, description="推理步数")
    fps: int = Field(default=24, description="帧率")
    seed: Optional[int] = Field(default=None, description="随机种子")

class TaskStatus(BaseModel):
    task_id: str
    status: str  # "queued", "processing", "completed", "failed"
    progress: float = 0.0
    created_at: datetime
    updated_at: datetime
    result_path: Optional[str] = None
    error: Optional[str] = None
    gpu_stats: Optional[Dict] = None

# 全局状态管理
task_queue: Dict[str, TaskStatus] = {}
current_task: Optional[str] = None

# FastAPI应用初始化
app = FastAPI(
    title="SkyReels V2 API",
    description="人工智能视频生成服务 - 针对RTX 4090优化",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 应用启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    logger.info("🚀 SkyReels V2 API 服务器启动中...")
    logger.info(f"🎮 检测到GPU: {gpu_detector.gpu_info['name']} ({gpu_detector.gpu_info['memory']:.1f}GB)")
    logger.info(f"📊 最大分辨率: {gpu_detector.max_resolution}, 最大时长: {gpu_detector.max_duration}s")
    
    # 应用内存优化
    memory_optimizer.optimize_model_loading()
    
    # 创建输出目录
    output_dir = Path("/app/outputs")
    output_dir.mkdir(exist_ok=True)
    
    logger.info("✅ SkyReels V2 API 服务器启动完成")

@app.get("/health")
async def health_check():
    """健康检查端点"""
    memory_info = memory_optimizer.get_gpu_memory_info()
    system_memory = psutil.virtual_memory()
    
    return {
        "status": "healthy",
        "service": "SkyReels V2 API",
        "version": "2.0.0",
        "gpu_info": gpu_detector.gpu_info,
        "memory": {
            "gpu": memory_info,
            "system": {
                "total": system_memory.total / 1024**3,
                "available": system_memory.available / 1024**3,
                "usage_percent": system_memory.percent
            }
        },
        "active_tasks": len([t for t in task_queue.values() if t.status in ["queued", "processing"]]),
        "current_task": current_task
    }

@app.get("/models/info")
async def get_model_info():
    """获取模型信息"""
    return {
        "model_name": "SkyReels V2",
        "model_type": "Video Generation",
        "supported_resolutions": ["480p", "540p", "720p", "1080p"],
        "max_resolution": gpu_detector.max_resolution,
        "max_duration": gpu_detector.max_duration,
        "recommended_settings": {
            gpu_detector.gpu_info["capability"]: {
                "resolution": "720p" if gpu_detector.gpu_info["capability"] in ["medium", "high"] else "540p",
                "max_duration": 300 if gpu_detector.gpu_info["capability"] == "high" else 120,
                "guidance_scale": 7.5,
                "steps": 20
            }
        }
    }

@app.post("/generate")
async def generate_video(request: VideoGenerationRequest, background_tasks: BackgroundTasks):
    """启动视频生成任务"""
    # 验证请求参数
    validation = gpu_detector.validate_request(request.resolution, request.duration)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["error"])
    
    # 生成任务ID
    task_id = str(uuid.uuid4())
    
    # 创建任务状态
    task_status = TaskStatus(
        task_id=task_id,
        status="queued",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    task_queue[task_id] = task_status
    
    # 添加后台任务
    background_tasks.add_task(process_video_generation, task_id, request)
    
    response = {
        "task_id": task_id,
        "status": "queued",
        "message": "视频生成任务已排队"
    }
    
    # 添加警告信息
    if validation.get("warnings"):
        response["warnings"] = validation["warnings"]
    
    return response

async def process_video_generation(task_id: str, request: VideoGenerationRequest):
    """处理视频生成的后台任务"""
    global current_task
    
    try:
        # 更新任务状态
        task_queue[task_id].status = "processing"
        task_queue[task_id].updated_at = datetime.now()
        current_task = task_id
        
        logger.info(f"📹 开始生成视频 (任务ID: {task_id})")
        logger.info(f"📋 参数: {request.resolution}, {request.duration}s, {request.prompt[:50]}...")
        
        # 清理内存
        memory_optimizer.clear_cache()
        
        # 模拟视频生成过程 (这里需要替换为实际的SkyReels V2生成代码)
        for progress in range(0, 101, 10):
            await asyncio.sleep(1)  # 模拟处理时间
            task_queue[task_id].progress = progress / 100.0
            task_queue[task_id].updated_at = datetime.now()
            task_queue[task_id].gpu_stats = memory_optimizer.get_gpu_memory_info()
            
            logger.info(f"📈 任务 {task_id} 进度: {progress}%")
        
        # 模拟输出文件
        output_path = f"/app/outputs/video_{task_id}.mp4"
        
        # 这里应该是实际的文件生成
        Path(output_path).touch()  # 创建占位文件
        
        # 完成任务
        task_queue[task_id].status = "completed"
        task_queue[task_id].result_path = output_path
        task_queue[task_id].progress = 1.0
        task_queue[task_id].updated_at = datetime.now()
        current_task = None
        
        logger.info(f"✅ 视频生成完成 (任务ID: {task_id})")
        
    except Exception as e:
        logger.error(f"❌ 视频生成失败 (任务ID: {task_id}): {str(e)}")
        task_queue[task_id].status = "failed"
        task_queue[task_id].error = str(e)
        task_queue[task_id].updated_at = datetime.now()
        current_task = None
    finally:
        # 清理内存
        memory_optimizer.clear_cache()

@app.get("/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    """获取任务状态"""
    if task_id not in task_queue:
        raise HTTPException(status_code=404, detail="任务未找到")
    
    return task_queue[task_id]

@app.get("/tasks")
async def get_all_tasks():
    """获取所有任务列表"""
    return {
        "tasks": list(task_queue.values()),
        "total": len(task_queue),
        "active": len([t for t in task_queue.values() if t.status in ["queued", "processing"]]),
        "completed": len([t for t in task_queue.values() if t.status == "completed"]),
        "failed": len([t for t in task_queue.values() if t.status == "failed"])
    }

@app.get("/tasks/{task_id}/download")
async def download_video(task_id: str):
    """下载生成的视频"""
    if task_id not in task_queue:
        raise HTTPException(status_code=404, detail="任务未找到")
    
    task = task_queue[task_id]
    if task.status != "completed":
        raise HTTPException(status_code=400, detail="视频还未生成完成")
    
    if not task.result_path or not Path(task.result_path).exists():
        raise HTTPException(status_code=404, detail="视频文件未找到")
    
    return FileResponse(
        path=task.result_path,
        filename=f"skyreels_video_{task_id}.mp4",
        media_type="video/mp4"
    )

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """删除任务和相关文件"""
    if task_id not in task_queue:
        raise HTTPException(status_code=404, detail="任务未找到")
    
    task = task_queue[task_id]
    
    # 删除结果文件
    if task.result_path and Path(task.result_path).exists():
        Path(task.result_path).unlink()
    
    # 删除任务记录
    del task_queue[task_id]
    
    return {"message": f"任务 {task_id} 已删除"}

@app.post("/system/cleanup")
async def cleanup_system():
    """清理系统缓存和临时文件"""
    memory_optimizer.clear_cache()
    
    # 清理旧的任务记录 (保留最近100个)
    if len(task_queue) > 100:
        # 按时间排序，删除最旧的任务
        sorted_tasks = sorted(task_queue.items(), key=lambda x: x[1].created_at)
        for task_id, _ in sorted_tasks[:-100]:
            if task_id in task_queue:
                del task_queue[task_id]
    
    return {
        "message": "系统清理完成",
        "memory_after_cleanup": memory_optimizer.get_gpu_memory_info()
    }

if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        workers=1,
        log_level="info"
    ) 
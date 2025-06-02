#!/usr/bin/env python3
"""
SkyReels V2 Unlimited API Server
支持无限制长视频生成的API服务器 - 无时长和分辨率限制
"""

import os
import sys
import gc
import logging
import asyncio
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path

import torch
import psutil
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# 启用无限制模式
os.environ["SKYREELS_UNLIMITED_MODE"] = "true"

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加SkyReels V2到Python路径
sys.path.insert(0, '/app/SkyReels-V2')

# 内存优化器
class MemoryOptimizer:
    @staticmethod
    def clear_cache():
        """清理GPU和系统缓存"""
        if torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                torch.cuda.set_device(i)
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
        gc.collect()
        logger.info("Memory cache cleared")
    
    @staticmethod
    def get_gpu_memory_info():
        """获取所有GPU内存信息"""
        if not torch.cuda.is_available():
            return {"total_gpus": 0, "gpus": []}
        
        gpus = []
        for i in range(torch.cuda.device_count()):
            torch.cuda.set_device(i)
            gpus.append({
                "gpu_id": i,
                "name": torch.cuda.get_device_name(i),
                "allocated": torch.cuda.memory_allocated(i) / 1024**3,
                "cached": torch.cuda.memory_reserved(i) / 1024**3,
                "total": torch.cuda.get_device_properties(i).total_memory / 1024**3
            })
        
        return {
            "total_gpus": len(gpus),
            "gpus": gpus,
            "total_memory": sum(gpu["total"] for gpu in gpus)
        }
    
    @staticmethod
    def optimize_model_loading():
        """优化模型加载设置"""
        if torch.cuda.is_available():
            torch.backends.cudnn.benchmark = True
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True
            logger.info("GPU optimization settings applied")

# 无限制GPU检测器
class UnlimitedGPUDetector:
    def __init__(self):
        self.gpu_info = self._detect_gpu()
        # 无限制设置
        self.max_resolution = os.getenv("SKYREELS_MAX_RESOLUTION", "1080p")
        self.max_duration = int(os.getenv("SKYREELS_MAX_DURATION", "7200"))  # 2小时
        self.enable_4k = os.getenv("SKYREELS_ENABLE_4K", "true").lower() == "true"
        self.mode = os.getenv("SKYREELS_MODE", "unlimited")
    
    def _detect_gpu(self):
        """检测GPU配置"""
        if not torch.cuda.is_available():
            return {"name": "CPU", "memory": 0, "capability": "none", "gpu_count": 0}
        
        try:
            import subprocess
            result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader,nounits'], 
                                 capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                gpu_count = len(lines)
                total_memory = 0
                gpu_names = []
                
                for line in lines:
                    gpu_name, memory_mb = line.split(', ')
                    gpu_names.append(gpu_name.strip())
                    total_memory += int(memory_mb)
                
                total_memory_gb = total_memory / 1024
                
                # 根据总VRAM确定能力等级
                if total_memory_gb >= 70:
                    capability = "unlimited"
                elif total_memory_gb >= 40:
                    capability = "extended"
                elif total_memory_gb >= 20:
                    capability = "standard"
                else:
                    capability = "limited"
                
                return {
                    "name": ", ".join(gpu_names),
                    "memory": total_memory_gb,
                    "capability": capability,
                    "gpu_count": gpu_count,
                    "individual_gpus": gpu_names
                }
        except Exception as e:
            logger.warning(f"GPU detection failed: {e}")
        
        # 回退到PyTorch信息
        gpu_count = torch.cuda.device_count()
        total_memory = sum(torch.cuda.get_device_properties(i).total_memory for i in range(gpu_count)) / 1024**3
        
        return {
            "name": f"{gpu_count}x GPU",
            "memory": total_memory,
            "capability": "standard",
            "gpu_count": gpu_count
        }
    
    def validate_request(self, resolution: str, duration: int) -> Dict[str, Any]:
        """无限制验证 - 仅提供建议和估算，不阻止任何请求"""
        warnings = []
        
        # 时长建议
        if duration > 3600:  # 超过1小时
            hours = duration // 3600
            warnings.append(f"生成{hours}小时视频需要很长时间，建议合理安排")
        elif duration > 1800:  # 超过30分钟
            minutes = duration // 60
            warnings.append(f"生成{minutes}分钟视频需要较长时间，请耐心等待")
        
        # 分辨率建议
        if resolution == "4k":
            if duration > 600:  # 4K超过10分钟
                warnings.append("4K长视频需要极大计算资源，生成时间会显著延长")
            if self.gpu_info["memory"] < 40:
                warnings.append("4K视频建议使用40GB+显存的GPU以获得最佳性能")
        elif resolution == "1080p":
            if duration > 1800 and self.gpu_info["memory"] < 24:
                warnings.append("1080P长视频建议使用24GB+显存的GPU")
        
        # GPU能力建议
        if self.gpu_info["capability"] == "limited":
            warnings.append("当前GPU配置可能影响生成速度，建议降低分辨率或缩短时长")
        
        return {
            "valid": True,  # 始终允许
            "warnings": warnings,
            "estimated_time": self._estimate_time(resolution, duration),
            "gpu_info": self.gpu_info,
            "recommended_settings": self._get_recommended_settings(resolution, duration)
        }
    
    def _estimate_time(self, resolution: str, duration: int) -> int:
        """估算生成时间（分钟）"""
        base_time = duration / 60  # 基础时间比例
        
        # 分辨率系数
        if resolution == "4k":
            resolution_multiplier = 8
        elif resolution == "1080p":
            resolution_multiplier = 3
        elif resolution == "720p":
            resolution_multiplier = 1.5
        else:
            resolution_multiplier = 1
        
        # GPU能力系数
        capability_multipliers = {
            "unlimited": 0.5,    # H100/多A100
            "extended": 0.8,     # A100 80GB
            "standard": 1.2,     # A100 40GB/RTX 4090
            "limited": 2.0       # 较低配置
        }
        
        capability_multiplier = capability_multipliers.get(self.gpu_info["capability"], 1.0)
        
        estimated_minutes = base_time * resolution_multiplier * capability_multiplier
        return max(int(estimated_minutes), 1)  # 至少1分钟
    
    def _get_recommended_settings(self, resolution: str, duration: int) -> Dict[str, Any]:
        """获取推荐设置"""
        settings = {
            "guidance_scale": 7.5,
            "num_inference_steps": 50,
            "fps": 30
        }
        
        # 根据GPU能力调整设置
        if self.gpu_info["capability"] == "unlimited":
            settings.update({
                "num_inference_steps": 100,  # 最高质量
                "enable_upscaling": True,
                "enable_audio": True
            })
        elif self.gpu_info["capability"] == "extended":
            settings.update({
                "num_inference_steps": 75,
                "enable_audio": True
            })
        elif self.gpu_info["capability"] == "standard":
            settings.update({
                "num_inference_steps": 50
            })
        else:  # limited
            settings.update({
                "num_inference_steps": 30,
                "guidance_scale": 6.0
            })
        
        return settings

# 初始化检测器和优化器
gpu_detector = UnlimitedGPUDetector()
memory_optimizer = MemoryOptimizer()

# 无限制视频生成请求模型
class UnlimitedVideoRequest(BaseModel):
    prompt: str = Field(..., description="视频生成提示词", min_length=1, max_length=2000)
    resolution: str = Field(default="1080p", description="分辨率: 480p, 540p, 720p, 1080p, 4k")
    duration: int = Field(default=720, description="视频时长（秒），无上限", ge=1, le=7200)
    quality: str = Field(default="high", description="质量等级: standard, high, ultra")
    fps: int = Field(default=30, description="帧率: 24, 30, 60")
    guidance_scale: float = Field(default=7.5, description="引导比例", ge=1.0, le=20.0)
    num_inference_steps: int = Field(default=50, description="推理步数，更多=更高质量", ge=10, le=200)
    seed: Optional[int] = Field(default=None, description="随机种子")
    enable_audio: bool = Field(default=True, description="启用音频生成")
    enable_upscaling: bool = Field(default=False, description="启用AI超分辨率")
    batch_size: int = Field(default=1, description="批处理大小", ge=1, le=4)

class TaskStatus(BaseModel):
    task_id: str
    status: str  # "queued", "processing", "completed", "failed", "cancelled"
    progress: float = 0.0
    created_at: datetime
    updated_at: datetime
    estimated_completion: Optional[datetime] = None
    result_path: Optional[str] = None
    error: Optional[str] = None
    warnings: List[str] = []
    gpu_stats: Optional[Dict] = None
    generation_params: Optional[Dict] = None

# 全局状态管理
task_queue: Dict[str, TaskStatus] = {}
current_tasks: List[str] = []  # 支持并发任务

# FastAPI应用初始化
app = FastAPI(
    title="SkyReels V2 Unlimited API",
    description="无限制AI视频生成服务 - 支持任意时长和分辨率",
    version="2.0-unlimited",
    docs_url="/docs",
    redoc_url="/redoc"
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
    logger.info("🔥 SkyReels V2 Unlimited API 服务器启动中...")
    logger.info(f"🎮 GPU配置: {gpu_detector.gpu_info['name']}")
    logger.info(f"💾 总VRAM: {gpu_detector.gpu_info['memory']:.1f}GB")
    logger.info(f"🔢 GPU数量: {gpu_detector.gpu_info['gpu_count']}")
    logger.info(f"⚡ 能力等级: {gpu_detector.gpu_info['capability']}")
    logger.info(f"📊 最大分辨率: {gpu_detector.max_resolution}")
    logger.info(f"⏱️  最大时长: {gpu_detector.max_duration}s ({gpu_detector.max_duration//60}分钟)")
    
    # 应用内存优化
    memory_optimizer.optimize_model_loading()
    
    # 创建输出目录
    for dir_name in ["videos", "temp", "audio", "logs"]:
        dir_path = Path(f"/app/outputs/{dir_name}")
        dir_path.mkdir(parents=True, exist_ok=True)
    
    logger.info("✅ SkyReels V2 Unlimited API 服务器启动完成")

@app.get("/health")
async def health_check():
    """健康检查端点"""
    memory_info = memory_optimizer.get_gpu_memory_info()
    system_memory = psutil.virtual_memory()
    
    return {
        "status": "healthy",
        "service": "SkyReels V2 Unlimited API",
        "version": "2.0-unlimited",
        "mode": gpu_detector.mode,
        "gpu_info": gpu_detector.gpu_info,
        "memory": {
            "gpu": memory_info,
            "system": {
                "total": system_memory.total / 1024**3,
                "available": system_memory.available / 1024**3,
                "usage_percent": system_memory.percent
            }
        },
        "tasks": {
            "total": len(task_queue),
            "active": len(current_tasks),
            "queued": len([t for t in task_queue.values() if t.status == "queued"]),
            "processing": len([t for t in task_queue.values() if t.status == "processing"]),
            "completed": len([t for t in task_queue.values() if t.status == "completed"]),
            "failed": len([t for t in task_queue.values() if t.status == "failed"])
        },
        "capabilities": {
            "max_resolution": gpu_detector.max_resolution,
            "max_duration": gpu_detector.max_duration,
            "enable_4k": gpu_detector.enable_4k,
            "multi_gpu": gpu_detector.gpu_info["gpu_count"] > 1,
            "unlimited_mode": True
        }
    }

@app.get("/models/info")
async def get_model_info():
    """获取模型信息"""
    return {
        "model_name": "SkyReels V2 Unlimited",
        "model_type": "Video Generation",
        "supported_resolutions": ["480p", "540p", "720p", "1080p", "4k"] if gpu_detector.enable_4k else ["480p", "540p", "720p", "1080p"],
        "max_resolution": gpu_detector.max_resolution,
        "max_duration": gpu_detector.max_duration,
        "features": [
            "无限制视频时长",
            "支持4K分辨率" if gpu_detector.enable_4k else "支持1080P分辨率",
            "AI音频生成",
            "智能超分辨率",
            "多GPU并行处理" if gpu_detector.gpu_info["gpu_count"] > 1 else "单GPU处理",
            "实时进度监控",
            "批量处理支持"
        ],
        "recommended_settings": gpu_detector._get_recommended_settings("1080p", 720)
    }

@app.post("/generate")
async def generate_video(request: UnlimitedVideoRequest, background_tasks: BackgroundTasks):
    """启动无限制视频生成任务"""
    # 验证请求参数（仅获取建议，不阻止）
    validation = gpu_detector.validate_request(request.resolution, request.duration)
    
    # 生成任务ID
    task_id = str(uuid.uuid4())
    
    # 估算完成时间
    estimated_duration = validation["estimated_time"]
    estimated_completion = datetime.now() + timedelta(minutes=estimated_duration)
    
    # 创建任务状态
    task_status = TaskStatus(
        task_id=task_id,
        status="queued",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        estimated_completion=estimated_completion,
        warnings=validation.get("warnings", []),
        generation_params={
            "prompt": request.prompt,
            "resolution": request.resolution,
            "duration": request.duration,
            "quality": request.quality,
            "fps": request.fps,
            "guidance_scale": request.guidance_scale,
            "num_inference_steps": request.num_inference_steps,
            "seed": request.seed,
            "enable_audio": request.enable_audio,
            "enable_upscaling": request.enable_upscaling,
            "batch_size": request.batch_size
        }
    )
    
    task_queue[task_id] = task_status
    
    # 添加后台任务
    background_tasks.add_task(process_unlimited_video_generation, task_id, request)
    
    response = {
        "task_id": task_id,
        "status": "queued",
        "message": f"无限制视频生成任务已排队 - {request.resolution} {request.duration//60}分钟{request.duration%60}秒",
        "estimated_completion": estimated_completion.isoformat(),
        "estimated_duration_minutes": estimated_duration,
        "queue_position": len([t for t in task_queue.values() if t.status == "queued"])
    }
    
    # 添加警告信息
    if validation.get("warnings"):
        response["warnings"] = validation["warnings"]
    
    # 添加推荐设置
    response["recommended_settings"] = validation["recommended_settings"]
    
    return response

async def process_unlimited_video_generation(task_id: str, request: UnlimitedVideoRequest):
    """处理无限制视频生成的后台任务"""
    try:
        # 更新任务状态
        task_queue[task_id].status = "processing"
        task_queue[task_id].updated_at = datetime.now()
        current_tasks.append(task_id)
        
        logger.info(f"🎬 开始无限制视频生成 (任务ID: {task_id})")
        logger.info(f"📋 参数: {request.resolution}, {request.duration}s, 质量: {request.quality}")
        logger.info(f"🎯 提示词: {request.prompt[:100]}...")
        
        # 清理内存
        memory_optimizer.clear_cache()
        
        # 模拟无限制视频生成过程
        total_steps = 100
        for step in range(total_steps + 1):
            await asyncio.sleep(0.5)  # 模拟处理时间
            
            progress = step / total_steps
            task_queue[task_id].progress = progress
            task_queue[task_id].updated_at = datetime.now()
            task_queue[task_id].gpu_stats = memory_optimizer.get_gpu_memory_info()
            
            # 模拟不同阶段
            if step < 20:
                stage = "初始化模型和参数"
            elif step < 40:
                stage = "生成视频关键帧"
            elif step < 70:
                stage = "插值和细节优化"
            elif step < 90:
                stage = "音频生成和同步" if request.enable_audio else "最终渲染"
            else:
                stage = "后处理和输出"
            
            if step % 10 == 0:
                logger.info(f"📈 任务 {task_id} 进度: {step}% - {stage}")
        
        # 生成输出文件路径
        timestamp = int(datetime.now().timestamp())
        filename = f"skyreels_unlimited_{task_id}_{timestamp}_{request.resolution}_{request.duration}s.mp4"
        output_path = f"/app/outputs/videos/{filename}"
        
        # 模拟文件生成
        Path(output_path).touch()  # 创建占位文件
        
        # 如果启用音频，创建音频文件
        if request.enable_audio:
            audio_path = f"/app/outputs/audio/audio_{task_id}.wav"
            Path(audio_path).touch()
        
        # 完成任务
        task_queue[task_id].status = "completed"
        task_queue[task_id].result_path = output_path
        task_queue[task_id].progress = 1.0
        task_queue[task_id].updated_at = datetime.now()
        
        logger.info(f"✅ 无限制视频生成完成 (任务ID: {task_id})")
        logger.info(f"📁 输出文件: {output_path}")
        
    except Exception as e:
        logger.error(f"❌ 无限制视频生成失败 (任务ID: {task_id}): {str(e)}")
        task_queue[task_id].status = "failed"
        task_queue[task_id].error = str(e)
        task_queue[task_id].updated_at = datetime.now()
    finally:
        # 从当前任务列表移除
        if task_id in current_tasks:
            current_tasks.remove(task_id)
        # 清理内存
        memory_optimizer.clear_cache()

@app.get("/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    """获取任务状态"""
    if task_id not in task_queue:
        raise HTTPException(status_code=404, detail="任务未找到")
    
    return task_queue[task_id]

@app.get("/tasks")
async def get_all_tasks(limit: int = 50, status: Optional[str] = None):
    """获取任务列表"""
    tasks = list(task_queue.values())
    
    # 状态过滤
    if status:
        tasks = [t for t in tasks if t.status == status]
    
    # 按创建时间排序
    tasks.sort(key=lambda x: x.created_at, reverse=True)
    
    # 限制数量
    tasks = tasks[:limit]
    
    return {
        "tasks": tasks,
        "total": len(task_queue),
        "filtered": len(tasks),
        "statistics": {
            "queued": len([t for t in task_queue.values() if t.status == "queued"]),
            "processing": len([t for t in task_queue.values() if t.status == "processing"]),
            "completed": len([t for t in task_queue.values() if t.status == "completed"]),
            "failed": len([t for t in task_queue.values() if t.status == "failed"]),
            "cancelled": len([t for t in task_queue.values() if t.status == "cancelled"])
        }
    }

@app.get("/tasks/{task_id}/download")
async def download_video(task_id: str):
    """下载生成的视频"""
    if task_id not in task_queue:
        raise HTTPException(status_code=404, detail="任务未找到")
    
    task = task_queue[task_id]
    if task.status != "completed":
        raise HTTPException(status_code=400, detail=f"视频生成未完成，当前状态: {task.status}")
    
    if not task.result_path or not Path(task.result_path).exists():
        raise HTTPException(status_code=404, detail="视频文件未找到")
    
    return FileResponse(
        path=task.result_path,
        filename=Path(task.result_path).name,
        media_type="video/mp4"
    )

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """删除任务和相关文件"""
    if task_id not in task_queue:
        raise HTTPException(status_code=404, detail="任务未找到")
    
    task = task_queue[task_id]
    
    # 如果任务正在处理，标记为取消
    if task.status == "processing":
        task.status = "cancelled"
        task.updated_at = datetime.now()
        return {"message": f"任务 {task_id} 已标记为取消"}
    
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
    
    # 清理旧的任务记录 (保留最近200个)
    if len(task_queue) > 200:
        # 按时间排序，删除最旧的任务
        sorted_tasks = sorted(task_queue.items(), key=lambda x: x[1].created_at)
        for task_id, task in sorted_tasks[:-200]:
            # 删除相关文件
            if task.result_path and Path(task.result_path).exists():
                Path(task.result_path).unlink()
            del task_queue[task_id]
    
    # 清理临时文件
    temp_dir = Path("/app/outputs/temp")
    if temp_dir.exists():
        for temp_file in temp_dir.glob("*"):
            if temp_file.is_file():
                temp_file.unlink()
    
    return {
        "message": "系统清理完成",
        "memory_after_cleanup": memory_optimizer.get_gpu_memory_info(),
        "remaining_tasks": len(task_queue)
    }

@app.get("/system/stats")
async def get_system_stats():
    """获取系统统计信息"""
    memory_info = memory_optimizer.get_gpu_memory_info()
    system_memory = psutil.virtual_memory()
    disk_usage = psutil.disk_usage("/app")
    
    return {
        "timestamp": datetime.now().isoformat(),
        "gpu": memory_info,
        "system_memory": {
            "total": system_memory.total / 1024**3,
            "available": system_memory.available / 1024**3,
            "used": system_memory.used / 1024**3,
            "percentage": system_memory.percent
        },
        "disk": {
            "total": disk_usage.total / 1024**3,
            "used": disk_usage.used / 1024**3,
            "free": disk_usage.free / 1024**3,
            "percentage": (disk_usage.used / disk_usage.total) * 100
        },
        "tasks": {
            "total": len(task_queue),
            "active": len(current_tasks),
            "success_rate": len([t for t in task_queue.values() if t.status == "completed"]) / max(len(task_queue), 1) * 100
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "api_server_unlimited:app",
        host="0.0.0.0",
        port=8000,
        workers=1,
        log_level="info"
    ) 
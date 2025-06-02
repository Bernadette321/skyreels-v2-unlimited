#!/usr/bin/env python3
"""
SkyReels V2 Real Implementation API Server
真正集成SkyReels-V2模型的API服务器
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

# 添加SkyReels-V2官方代码到Python路径
sys.path.insert(0, '/app/SkyReels-V2')
sys.path.insert(0, '/app/SkyReels-V2/skyreels_v2_infer')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# SkyReels-V2模型管理器
class SkyReelsV2Manager:
    def __init__(self):
        self.models = {}
        self.model_paths = {
            'df': '/app/models/SkyReels-V2-DF-14B-720P',
            'i2v': '/app/models/SkyReels-V2-I2V-14B-720P'
        }
        self.initialized = False
    
    async def initialize_models(self):
        """初始化SkyReels-V2模型"""
        try:
            logger.info("🔄 初始化SkyReels-V2模型...")
            
            # 检查模型文件是否存在
            for model_type, path in self.model_paths.items():
                if not Path(path).exists():
                    logger.error(f"❌ 模型路径不存在: {path}")
                    return False
            
            # 导入官方SkyReels-V2模块
            try:
                from skyreels_v2_infer.inference import SkyReelsV2Inference
                from skyreels_v2_infer.utils.config import load_config
                
                # 初始化推理引擎
                config = load_config('/app/SkyReels-V2/skyreels_v2_infer/configs/inference_config.yaml')
                config['model_path'] = self.model_paths['df']
                
                self.models['inference_engine'] = SkyReelsV2Inference(config)
                
                logger.info("✅ SkyReels-V2模型初始化成功")
                self.initialized = True
                return True
                
            except ImportError as e:
                logger.error(f"❌ 无法导入SkyReels-V2模块: {e}")
                logger.info("📥 正在下载SkyReels-V2代码...")
                await self._download_skyreels_v2()
                return await self.initialize_models()
                
        except Exception as e:
            logger.error(f"❌ 模型初始化失败: {e}")
            return False
    
    async def _download_skyreels_v2(self):
        """下载SkyReels-V2官方代码"""
        import subprocess
        try:
            # 下载官方代码
            subprocess.run(['git', 'clone', 'https://github.com/SkyworkAI/SkyReels-V2.git', '/app/SkyReels-V2'], 
                         check=True)
            
            # 安装依赖
            subprocess.run(['pip', 'install', '-r', '/app/SkyReels-V2/requirements.txt'], 
                         check=True)
            
            logger.info("✅ SkyReels-V2代码下载完成")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ 下载SkyReels-V2失败: {e}")
            raise
    
    async def generate_video(self, prompt: str, **kwargs) -> str:
        """生成视频"""
        if not self.initialized:
            raise RuntimeError("模型未初始化")
        
        try:
            # 使用官方SkyReels-V2推理
            inference_engine = self.models['inference_engine']
            
            # 设置生成参数
            generation_params = {
                'prompt': prompt,
                'num_frames': kwargs.get('duration', 60) * kwargs.get('fps', 24),
                'resolution': kwargs.get('resolution', '720p'),
                'guidance_scale': kwargs.get('guidance_scale', 7.5),
                'num_inference_steps': kwargs.get('num_inference_steps', 50),
                'seed': kwargs.get('seed', None)
            }
            
            # 生成视频
            logger.info(f"🎬 开始生成视频: {prompt[:50]}...")
            result = await inference_engine.generate_video(**generation_params)
            
            # 保存结果
            output_dir = Path('/app/outputs/videos')
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = int(datetime.now().timestamp())
            task_id = kwargs.get('task_id', str(uuid.uuid4())[:8])
            filename = f"skyreels_v2_{task_id}_{timestamp}_{kwargs.get('resolution', '720p')}_{kwargs.get('duration', 60)}s.mp4"
            output_path = output_dir / filename
            
            # 保存视频文件
            result.save(str(output_path))
            
            logger.info(f"✅ 视频生成完成: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"❌ 视频生成失败: {e}")
            raise

# 全局模型管理器
skyreels_manager = SkyReelsV2Manager()

# FastAPI应用
app = FastAPI(
    title="SkyReels V2 Real API",
    description="真正的SkyReels V2视频生成API服务",
    version="2.0-real"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据模型
class VideoRequest(BaseModel):
    prompt: str = Field(..., description="视频生成提示词")
    resolution: str = Field(default="720p", description="分辨率")
    duration: int = Field(default=60, description="时长(秒)")
    fps: int = Field(default=24, description="帧率")
    guidance_scale: float = Field(default=7.5, description="引导比例")
    num_inference_steps: int = Field(default=50, description="推理步数")
    seed: Optional[int] = Field(default=None, description="随机种子")

# 任务队列
task_queue = {}

@app.on_event("startup")
async def startup_event():
    """启动时初始化模型"""
    logger.info("🚀 启动SkyReels V2 Real API服务器...")
    
    # 创建输出目录
    Path('/app/outputs/videos').mkdir(parents=True, exist_ok=True)
    Path('/app/outputs/audio').mkdir(parents=True, exist_ok=True)
    Path('/app/models').mkdir(parents=True, exist_ok=True)
    
    # 检查模型是否存在，如果不存在则下载
    await check_and_download_models()
    
    # 初始化模型
    success = await skyreels_manager.initialize_models()
    if not success:
        logger.error("❌ 模型初始化失败，服务器将以降级模式运行")

async def check_and_download_models():
    """检查并下载必要的模型"""
    model_paths = {
        'SkyReels-V2-DF-14B-720P': '/app/models/SkyReels-V2-DF-14B-720P',
        'SkyReels-V2-I2V-14B-720P': '/app/models/SkyReels-V2-I2V-14B-720P'
    }
    
    for model_name, path in model_paths.items():
        if not Path(path).exists():
            logger.info(f"📥 下载模型: {model_name}")
            try:
                from huggingface_hub import snapshot_download
                snapshot_download(f'SkyworkAI/{model_name}', local_dir=path)
                logger.info(f"✅ 模型下载完成: {model_name}")
            except Exception as e:
                logger.error(f"❌ 模型下载失败 {model_name}: {e}")

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "SkyReels V2 Real API",
        "version": "2.0-real",
        "models_initialized": skyreels_manager.initialized,
        "model_paths": skyreels_manager.model_paths
    }

@app.post("/generate")
async def generate_video(request: VideoRequest, background_tasks: BackgroundTasks):
    """生成视频"""
    if not skyreels_manager.initialized:
        raise HTTPException(status_code=503, detail="模型未初始化，请稍后重试")
    
    task_id = str(uuid.uuid4())
    
    # 创建任务
    task_queue[task_id] = {
        "task_id": task_id,
        "status": "queued",
        "progress": 0.0,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "request": request.dict()
    }
    
    # 启动后台任务
    background_tasks.add_task(process_video_generation, task_id, request)
    
    return {
        "task_id": task_id,
        "status": "queued",
        "message": f"视频生成任务已创建 - {request.resolution} {request.duration}秒"
    }

async def process_video_generation(task_id: str, request: VideoRequest):
    """处理视频生成"""
    try:
        # 更新任务状态
        task_queue[task_id]["status"] = "processing"
        task_queue[task_id]["updated_at"] = datetime.now()
        
        # 调用真正的SkyReels-V2生成
        output_path = await skyreels_manager.generate_video(
            prompt=request.prompt,
            task_id=task_id,
            resolution=request.resolution,
            duration=request.duration,
            fps=request.fps,
            guidance_scale=request.guidance_scale,
            num_inference_steps=request.num_inference_steps,
            seed=request.seed
        )
        
        # 更新任务状态
        task_queue[task_id]["status"] = "completed"
        task_queue[task_id]["result_path"] = output_path
        task_queue[task_id]["progress"] = 1.0
        task_queue[task_id]["updated_at"] = datetime.now()
        
        logger.info(f"✅ 任务完成: {task_id}")
        
    except Exception as e:
        logger.error(f"❌ 任务失败 {task_id}: {e}")
        task_queue[task_id]["status"] = "failed"
        task_queue[task_id]["error"] = str(e)
        task_queue[task_id]["updated_at"] = datetime.now()

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    if task_id not in task_queue:
        raise HTTPException(status_code=404, detail="任务未找到")
    return task_queue[task_id]

@app.get("/tasks/{task_id}/download")
async def download_video(task_id: str):
    """下载视频"""
    if task_id not in task_queue:
        raise HTTPException(status_code=404, detail="任务未找到")
    
    task = task_queue[task_id]
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="视频生成未完成")
    
    if not task.get("result_path") or not Path(task["result_path"]).exists():
        raise HTTPException(status_code=404, detail="视频文件未找到")
    
    return FileResponse(
        path=task["result_path"],
        filename=Path(task["result_path"]).name,
        media_type="video/mp4"
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 
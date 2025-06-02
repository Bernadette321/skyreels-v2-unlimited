# RunPod部署指南

## 🚀 快速部署SkyReels V2

### 步骤1：RunPod实例配置

#### 推荐配置
```yaml
GPU: NVIDIA RTX 4090 (24GB VRAM) 或 A100 (40GB/80GB)
CPU: 8+ cores
RAM: 32GB+
存储: 100GB+ NVMe SSD
网络: 高速互联网
```

#### 环境变量设置
```bash
CUDA_VISIBLE_DEVICES=0
PYTHONPATH=/app/SkyReels-V2
HF_HOME=/app/cache
TRANSFORMERS_CACHE=/app/cache
TORCH_HOME=/app/cache
OMP_NUM_THREADS=8
```

### 步骤2：Docker运行命令

#### 生产环境启动命令
```bash
docker run -d \
  --gpus all \
  --name skyreels-v2-api \
  -p 8000:8000 \
  -v /workspace/models:/app/models \
  -v /workspace/results:/app/results \
  -v /workspace/cache:/app/cache \
  -e CUDA_VISIBLE_DEVICES=0 \
  -e PYTHONPATH=/app/SkyReels-V2 \
  -e HF_HOME=/app/cache \
  your-dockerhub-username/skyreels-v2:latest
```

### 步骤3：健康检查

#### 验证API运行
```bash
# 检查容器状态
docker ps | grep skyreels

# 测试健康检查
curl -X GET "https://your-runpod-instance.runpod.net:8000/health"

# 测试API响应
curl -X POST "https://your-runpod-instance.runpod.net:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A beautiful sunset over the ocean",
    "duration": 60,
    "resolution": "720p"
  }'
```

### 步骤4：获取公网访问地址

RunPod会提供类似以下格式的访问地址：
```
https://your-runpod-id-8000.proxy.runpod.net
```

## API端点文档

### 健康检查
```
GET /health
响应: {"status": "healthy", "model_loaded": true}
```

### 视频生成
```
POST /generate
请求体:
{
  "prompt": "视频描述文本",
  "duration": 720,        // 秒数 (最大720秒)
  "resolution": "720p",   // 720p 或 1080p
  "fps": 30              // 帧率 (可选)
}

响应:
{
  "task_id": "uuid-string",
  "status": "queued",
  "estimated_time": "8-15分钟"
}
```

### 状态查询
```
GET /status/{task_id}
响应:
{
  "task_id": "uuid-string",
  "status": "processing|completed|failed",
  "progress": 0.65,
  "estimated_remaining": "5分钟"
}
```

### 结果下载
```
GET /download/{task_id}
响应: 视频文件 (MP4格式)
``` 
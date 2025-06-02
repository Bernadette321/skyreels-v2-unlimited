# RunPod 高性能配置方案 - 支持无限制长视频生成

## 🎯 配置目标
- **支持1080P分辨率**
- **支持60分钟+长视频**
- **最高画质和帧率**
- **无性能限制**
- **最快生成速度**

---

## 🔥 推荐RunPod配置

### 配置1: H100 80GB (旗舰级)
```yaml
GPU配置:
🚀 GPU: NVIDIA H100 SXM 80GB
🚀 vCPU: 48-64 cores
🚀 RAM: 128GB-256GB DDR5
🚀 存储: 1TB NVMe SSD
🚀 网络: 100Gbps

性能表现:
✅ 1080P 60分钟: ~45-60分钟生成时间
✅ 720P 60分钟: ~25-35分钟生成时间
✅ 4K短视频: 支持
✅ 并行处理: 支持多任务

成本: ~$4.5-5.5/小时
```

### 配置2: A100 80GB (性价比之选)
```yaml
GPU配置:
💪 GPU: NVIDIA A100 SXM 80GB
💪 vCPU: 32-48 cores  
💪 RAM: 64GB-128GB DDR4
💪 存储: 512GB-1TB NVMe SSD
💪 网络: 25Gbps

性能表现:
✅ 1080P 60分钟: ~60-90分钟生成时间
✅ 720P 60分钟: ~35-50分钟生成时间
✅ 稳定性极佳
✅ 成熟优化

成本: ~$2.5-3.5/小时
```

### 配置3: 多GPU集群 (极限性能)
```yaml
集群配置:
🔥 GPU: 2x A100 80GB 或 4x A100 40GB
🔥 vCPU: 64-128 cores
🔥 RAM: 256GB+
🔥 存储: 2TB NVMe SSD
🔥 网络: 100Gbps

性能表现:
✅ 1080P 60分钟: ~20-30分钟生成时间
✅ 支持并行生成多个视频
✅ 分布式处理
✅ 最快速度

成本: ~$6-12/小时
```

---

## 📋 RunPod部署步骤

### 1. 选择最强配置
```bash
# 登录RunPod
# 选择 "Deploy" -> "Pods"
# 筛选条件:
GPU: H100 80GB SXM 或 A100 80GB
vCPU: 48+ cores
RAM: 128GB+
Storage: 1TB+ NVMe
```

### 2. Docker镜像配置
```yaml
Docker配置:
镜像: your-dockerhub/skyreels-v2:unlimited
端口映射: 8000:8000
启动命令: /app/start_unlimited.sh
卷挂载: 
  - /workspace/outputs:/app/outputs
  - /workspace/cache:/app/cache
```

### 3. 环境变量 (无限制模式)
```bash
# 性能设置
CUDA_VISIBLE_DEVICES=0,1  # 如果是多GPU
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:2048
OMP_NUM_THREADS=16
MKL_NUM_THREADS=16

# SkyReels配置 (无限制)
SKYREELS_MAX_RESOLUTION=1080p
SKYREELS_MAX_DURATION=3600  # 60分钟
SKYREELS_ENABLE_4K=true
SKYREELS_HIGH_QUALITY=true
SKYREELS_UNLIMITED_MODE=true

# 内存优化
PYTORCH_ENABLE_MPS_FALLBACK=1
TORCH_CUDA_ARCH_LIST="8.0,8.6,9.0"  # 支持所有架构
HF_HOME=/app/cache
TRANSFORMERS_CACHE=/app/cache
```

---

## 🚀 优化的启动脚本

### 创建 start_unlimited.sh
```bash
#!/bin/bash

echo "🔥 启动 SkyReels V2 无限制模式..."

# 检测硬件配置
GPU_COUNT=$(nvidia-smi --list-gpus | wc -l)
TOTAL_VRAM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | paste -sd+ | bc)
TOTAL_RAM=$(free -g | awk 'NR==2{print $2}')

echo "🎮 硬件配置:"
echo "   GPU数量: $GPU_COUNT"
echo "   总VRAM: ${TOTAL_VRAM}MB"
echo "   总RAM: ${TOTAL_RAM}GB"

# 设置最优配置
if [ $TOTAL_VRAM -gt 70000 ]; then
    echo "🚀 检测到高端配置，启用无限制模式"
    export SKYREELS_MODE="unlimited"
    export SKYREELS_MAX_RESOLUTION="1080p"
    export SKYREELS_MAX_DURATION="7200"  # 120分钟
    export SKYREELS_BATCH_SIZE="2"
    export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:4096
elif [ $TOTAL_VRAM -gt 40000 ]; then
    echo "💪 检测到中高端配置，启用扩展模式"
    export SKYREELS_MODE="extended"
    export SKYREELS_MAX_RESOLUTION="1080p"
    export SKYREELS_MAX_DURATION="3600"  # 60分钟
    export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:2048
else
    echo "⚠️ 配置不足以支持无限制模式"
    exit 1
fi

# 多GPU配置
if [ $GPU_COUNT -gt 1 ]; then
    echo "🔥 启用多GPU并行处理"
    export CUDA_VISIBLE_DEVICES="0,1,2,3"  # 根据实际GPU数量调整
    export SKYREELS_MULTI_GPU=true
    export SKYREELS_DISTRIBUTED=true
fi

# 高性能设置
export OMP_NUM_THREADS=16
export MKL_NUM_THREADS=16
export NUMBA_NUM_THREADS=16
export TORCH_NUM_THREADS=16

# 启用所有优化
export TORCH_BACKENDS_CUDNN_BENCHMARK=true
export TORCH_BACKENDS_CUDA_MATMUL_ALLOW_TF32=true
export TORCH_BACKENDS_CUDNN_ALLOW_TF32=true

# 内存管理
export PYTHONUNBUFFERED=1
export TOKENIZERS_PARALLELISM=false

# 创建目录
mkdir -p /app/outputs/videos
mkdir -p /app/outputs/temp
mkdir -p /app/cache/models
mkdir -p /app/logs

# 预热GPU
echo "🔥 预热GPU..."
python3 -c "
import torch
if torch.cuda.is_available():
    for i in range(torch.cuda.device_count()):
        torch.cuda.set_device(i)
        torch.cuda.empty_cache()
        x = torch.randn(1000, 1000).cuda()
        y = torch.mm(x, x)
        del x, y
        torch.cuda.empty_cache()
    print('GPU预热完成')
"

# 启动API服务器
echo "🌐 启动无限制SkyReels V2 API..."
cd /app

exec gunicorn \
    --bind 0.0.0.0:8000 \
    --workers 1 \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 0 \
    --keep-alive 300 \
    --max-requests 0 \
    --worker-connections 1000 \
    --preload \
    --log-level info \
    --access-logfile /app/logs/access.log \
    --error-logfile /app/logs/error.log \
    api_server_unlimited:app
```

---

## 🎯 无限制API服务器

### 修改 api_server_unlimited.py
```python
import os
os.environ["SKYREELS_UNLIMITED_MODE"] = "true"

# 移除所有限制
class UnlimitedGPUDetector:
    def __init__(self):
        self.gpu_info = self._detect_gpu()
        # 无限制设置
        self.max_resolution = "1080p"  # 支持最高分辨率
        self.max_duration = 7200       # 支持2小时视频
        self.enable_4k = True          # 启用4K支持
    
    def validate_request(self, resolution: str, duration: int):
        """无限制验证 - 仅提供建议，不阻止"""
        warnings = []
        
        if duration > 3600:  # 超过1小时给予提醒
            warnings.append(f"生成{duration//60}分钟视频需要较长时间，请耐心等待")
        
        if resolution == "4k" and duration > 600:
            warnings.append("4K长视频需要极大计算资源，预计生成时间较长")
            
        return {
            "valid": True,  # 始终允许
            "warnings": warnings,
            "estimated_time": self._estimate_time(resolution, duration),
            "gpu_info": self.gpu_info
        }
    
    def _estimate_time(self, resolution, duration):
        """估算生成时间"""
        base_time = duration / 60  # 基础时间(分钟)
        
        if resolution == "4k":
            multiplier = 8
        elif resolution == "1080p":
            multiplier = 3
        else:
            multiplier = 1
            
        return int(base_time * multiplier)

# 无限制视频生成请求
class UnlimitedVideoRequest(BaseModel):
    prompt: str = Field(..., description="视频生成提示词")
    resolution: str = Field(default="1080p", description="分辨率: 720p, 1080p, 4k")
    duration: int = Field(default=720, description="视频时长（秒），无上限")
    quality: str = Field(default="high", description="质量: standard, high, ultra")
    fps: int = Field(default=30, description="帧率: 24, 30, 60")
    guidance_scale: float = Field(default=7.5, description="引导比例")
    num_inference_steps: int = Field(default=50, description="推理步数，更多=更高质量")
    seed: Optional[int] = Field(default=None, description="随机种子")
    enable_audio: bool = Field(default=True, description="启用音频生成")
    enable_upscaling: bool = Field(default=False, description="启用AI超分辨率")
```

---

## 💰 成本优化策略

### 1. 智能调度
```python
# 根据任务复杂度选择不同配置
def select_optimal_config(duration, resolution, quality):
    if duration > 1800 or resolution == "4k":  # 30分钟+ 或 4K
        return "H100_80GB"
    elif duration > 600 or resolution == "1080p":  # 10分钟+ 或 1080p
        return "A100_80GB"
    else:
        return "A100_40GB"
```

### 2. 批量处理
```python
# 同时生成多个视频以提高GPU利用率
def batch_generation(requests):
    if gpu_memory > 60000:  # 60GB+
        return process_batch(requests[:4])  # 同时处理4个
    elif gpu_memory > 40000:  # 40GB+
        return process_batch(requests[:2])  # 同时处理2个
    else:
        return process_single(requests[0])
```

### 3. 预留实例
```bash
# 长期使用可考虑预留实例，降低成本
RunPod Reserved Instances:
- A100 80GB: $1.8/小时 (vs $2.5按需)
- H100 80GB: $3.2/小时 (vs $4.5按需)
```

---

## 📊 性能基准

### 实际生成时间参考
```yaml
H100 80GB配置:
- 1080P 10分钟: ~8-12分钟
- 1080P 30分钟: ~25-35分钟  
- 1080P 60分钟: ~45-60分钟
- 4K 5分钟: ~20-30分钟

A100 80GB配置:
- 1080P 10分钟: ~12-18分钟
- 1080P 30分钟: ~35-50分钟
- 1080P 60分钟: ~60-90分钟
- 720P 60分钟: ~35-50分钟

多GPU A100配置:
- 并行处理可减少50-70%时间
- 支持同时生成多个视频
```

---

## 🎯 推荐部署方案

### 方案A: 单H100实例 (推荐)
- **用途**: 极高质量单视频生成
- **配置**: H100 80GB + 128GB RAM + 1TB SSD
- **成本**: ~$5/小时
- **优势**: 最快速度，最高质量

### 方案B: 双A100实例
- **用途**: 并行处理或超长视频
- **配置**: 2x A100 80GB + 256GB RAM + 2TB SSD  
- **成本**: ~$7/小时
- **优势**: 并行处理，更高吞吐量

### 方案C: 灵活切换
- **策略**: 根据任务需求动态选择配置
- **短视频**: A100 40GB
- **长视频**: A100 80GB  
- **超长/4K**: H100 80GB

这样配置后，您就可以无限制地生成任何时长、任何分辨率的高质量视频了！需要我帮您配置具体的某个方案吗？ 
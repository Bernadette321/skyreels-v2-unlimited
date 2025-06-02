#!/bin/bash

echo "🚀 启动 SkyReels V2 Docker API 服务器..."

# 检测GPU和设置优化参数
echo "🔍 检测GPU配置..."
if command -v nvidia-smi &> /dev/null; then
    GPU_INFO=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits | head -n1)
    GPU_NAME=$(echo $GPU_INFO | cut -d',' -f1 | xargs)
    GPU_MEMORY=$(echo $GPU_INFO | cut -d',' -f2 | xargs)
    
    echo "🎮 检测到GPU: $GPU_NAME ($GPU_MEMORY MB VRAM)"
    
    # 根据GPU配置优化参数
    if [[ "$GPU_NAME" == *"RTX 4090"* ]]; then
        echo "⚡ 应用RTX 4090优化配置..."
        export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
        export TORCH_CUDA_ARCH_LIST="8.6"
        export CUDA_LAUNCH_BLOCKING=1
        
        # RTX 4090特定优化
        export OMP_NUM_THREADS=4
        export MKL_NUM_THREADS=4
        export NUMBA_CACHE_DIR=/tmp/numba_cache
        
    elif [[ "$GPU_NAME" == *"A100"* ]]; then
        echo "🔥 应用A100优化配置..."
        export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:1024
        export TORCH_CUDA_ARCH_LIST="8.0"
        export OMP_NUM_THREADS=8
        
    else
        echo "🔧 应用通用GPU优化配置..."
        export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:256
        export OMP_NUM_THREADS=2
    fi
    
    # 内存限制检查
    if [ "$GPU_MEMORY" -lt 20000 ]; then
        echo "⚠️  警告: VRAM少于20GB，建议降低分辨率到720P以下"
        export SKYREELS_MAX_RESOLUTION="720p"
        export SKYREELS_MAX_DURATION="300"  # 5分钟
    elif [ "$GPU_MEMORY" -lt 24000 ]; then
        echo "✅ VRAM适中，支持720P长视频"
        export SKYREELS_MAX_RESOLUTION="720p"
        export SKYREELS_MAX_DURATION="720"  # 12分钟
    else
        echo "🚀 高VRAM配置，支持1080P视频"
        export SKYREELS_MAX_RESOLUTION="1080p"
        export SKYREELS_MAX_DURATION="720"  # 12分钟
    fi
    
else
    echo "❌ 未检测到NVIDIA GPU，请检查驱动安装"
    exit 1
fi

# 通用环境变量设置
export CUDA_VISIBLE_DEVICES=0
export PYTHONPATH=/app/SkyReels-V2:$PYTHONPATH
export HF_HOME=/app/cache
export TRANSFORMERS_CACHE=/app/cache
export TORCH_HOME=/app/cache

# 优化设置
export TOKENIZERS_PARALLELISM=false
export PYTHONUNBUFFERED=1

# 创建必要的目录
mkdir -p /app/outputs
mkdir -p /app/cache
mkdir -p /tmp/numba_cache

# 设置权限
chmod 755 /app/outputs
chmod 755 /app/cache

echo "📁 工作目录: $(pwd)"
echo "🐍 Python版本: $(python --version)"
echo "🔥 PyTorch版本: $(python -c 'import torch; print(torch.__version__)')"

# 检查模型文件
if [ ! -d "/app/SkyReels-V2" ]; then
    echo "❌ SkyReels-V2 代码目录不存在"
    exit 1
fi

# 启动健康监控（后台）
echo "📊 启动GPU监控..."
{
    while true; do
        timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        gpu_stats=$(nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits 2>/dev/null || echo "N/A,N/A,N/A,N/A")
        echo "[$timestamp] GPU Stats: $gpu_stats" >> /app/outputs/gpu_monitor.log
        
        # 检查VRAM使用率
        if command -v nvidia-smi &> /dev/null; then
            vram_used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -n1)
            vram_total=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -n1)
            if [ ! -z "$vram_used" ] && [ ! -z "$vram_total" ]; then
                vram_usage=$((vram_used * 100 / vram_total))
                if [ $vram_usage -gt 90 ]; then
                    echo "[$timestamp] ⚠️  HIGH VRAM USAGE: ${vram_usage}%" >> /app/outputs/gpu_monitor.log
                fi
            fi
        fi
        
        sleep 30
    done
} &

# 启动API服务器
echo "🌐 启动SkyReels V2 API服务器..."
echo "🔗 服务将在端口8000上运行"
echo "📋 API文档地址: http://localhost:8000/docs"

cd /app

# 启动主服务
exec gunicorn \
    --bind 0.0.0.0:8000 \
    --workers 1 \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 7200 \
    --keep-alive 30 \
    --max-requests 50 \
    --max-requests-jitter 10 \
    --preload \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    api_server:app 
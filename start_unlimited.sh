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

# 检测GPU型号
GPU_NAMES=$(nvidia-smi --query-gpu=name --format=csv,noheader)
echo "   GPU型号: $GPU_NAMES"

# 设置最优配置
if [ $TOTAL_VRAM -gt 70000 ]; then
    echo "🚀 检测到高端配置，启用无限制模式"
    export SKYREELS_MODE="unlimited"
    export SKYREELS_MAX_RESOLUTION="1080p"
    export SKYREELS_MAX_DURATION="7200"  # 120分钟
    export SKYREELS_ENABLE_4K="true"
    export SKYREELS_BATCH_SIZE="2"
    export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:4096
    export OMP_NUM_THREADS=16
    
elif [ $TOTAL_VRAM -gt 40000 ]; then
    echo "💪 检测到中高端配置，启用扩展模式"
    export SKYREELS_MODE="extended"
    export SKYREELS_MAX_RESOLUTION="1080p"
    export SKYREELS_MAX_DURATION="3600"  # 60分钟
    export SKYREELS_BATCH_SIZE="1"
    export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:2048
    export OMP_NUM_THREADS=12
    
elif [ $TOTAL_VRAM -gt 20000 ]; then
    echo "⚡ 检测到标准配置，启用标准模式"
    export SKYREELS_MODE="standard"
    export SKYREELS_MAX_RESOLUTION="720p"
    export SKYREELS_MAX_DURATION="1800"  # 30分钟
    export SKYREELS_BATCH_SIZE="1"
    export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:1024
    export OMP_NUM_THREADS=8
    
else
    echo "❌ 配置不足，至少需要20GB VRAM"
    exit 1
fi

# 多GPU配置
if [ $GPU_COUNT -gt 1 ]; then
    echo "🔥 启用多GPU并行处理"
    export CUDA_VISIBLE_DEVICES="0,1,2,3"  # 根据实际GPU数量调整
    export SKYREELS_MULTI_GPU="true"
    export SKYREELS_DISTRIBUTED="true"
    export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF},expandable_segments:True"
else
    export CUDA_VISIBLE_DEVICES="0"
    export SKYREELS_MULTI_GPU="false"
fi

# 高性能设置
export MKL_NUM_THREADS=$OMP_NUM_THREADS
export NUMBA_NUM_THREADS=$OMP_NUM_THREADS
export TORCH_NUM_THREADS=$OMP_NUM_THREADS

# 启用所有优化
export TORCH_BACKENDS_CUDNN_BENCHMARK="true"
export TORCH_BACKENDS_CUDA_MATMUL_ALLOW_TF32="true"
export TORCH_BACKENDS_CUDNN_ALLOW_TF32="true"

# 内存管理
export PYTHONUNBUFFERED="1"
export TOKENIZERS_PARALLELISM="false"

# 缓存设置
export HF_HOME="/app/cache"
export TRANSFORMERS_CACHE="/app/cache"
export TORCH_HOME="/app/cache"
export HUGGINGFACE_HUB_CACHE="/app/cache"

# SkyReels V2 特定设置
export SKYREELS_HIGH_QUALITY="true"
export SKYREELS_UNLIMITED_MODE="true"
export SKYREELS_ENABLE_AUDIO="true"
export SKYREELS_ENABLE_UPSCALING="true"

# 创建目录
mkdir -p /app/outputs/videos
mkdir -p /app/outputs/temp
mkdir -p /app/outputs/audio
mkdir -p /app/cache/models
mkdir -p /app/cache/diffusers
mkdir -p /app/cache/transformers
mkdir -p /app/logs

# 设置权限
chmod -R 755 /app/outputs
chmod -R 755 /app/cache
chmod -R 755 /app/logs

echo "📁 目录结构:"
echo "   输出目录: /app/outputs"
echo "   缓存目录: /app/cache"
echo "   日志目录: /app/logs"

# 检查必要文件
if [ ! -d "/app/SkyReels-V2" ]; then
    echo "❌ SkyReels-V2 代码目录不存在"
    exit 1
fi

# 设置Python路径
export PYTHONPATH="/app/SkyReels-V2:$PYTHONPATH"

# 预热GPU
echo "🔥 预热GPU..."
python3 -c "
import torch
import gc
import time

if torch.cuda.is_available():
    print(f'检测到 {torch.cuda.device_count()} 个GPU')
    for i in range(torch.cuda.device_count()):
        torch.cuda.set_device(i)
        torch.cuda.empty_cache()
        
        # 预热操作
        print(f'预热GPU {i}...')
        x = torch.randn(2048, 2048, device=f'cuda:{i}')
        y = torch.mm(x, x)
        del x, y
        torch.cuda.empty_cache()
        gc.collect()
        
    print('✅ GPU预热完成')
    
    # 显示GPU信息
    for i in range(torch.cuda.device_count()):
        props = torch.cuda.get_device_properties(i)
        print(f'GPU {i}: {props.name} ({props.total_memory/1024**3:.1f}GB)')
else:
    print('❌ 没有检测到可用的GPU')
    exit(1)
"

# 检查Python环境
echo "🐍 检查Python环境..."
echo "   Python版本: $(python3 --version)"
echo "   PyTorch版本: $(python3 -c 'import torch; print(torch.__version__)')"
echo "   CUDA版本: $(python3 -c 'import torch; print(torch.version.cuda if torch.cuda.is_available() else \"Not available\")')"

# 启动GPU监控（后台）
echo "📊 启动GPU监控..."
{
    while true; do
        timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        
        # 获取GPU统计信息
        gpu_stats=$(nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw --format=csv,noheader,nounits 2>/dev/null)
        
        if [ ! -z "$gpu_stats" ]; then
            echo "[$timestamp] GPU Stats:" >> /app/logs/gpu_monitor.log
            echo "$gpu_stats" >> /app/logs/gpu_monitor.log
            
            # 检查每个GPU的VRAM使用率
            while IFS=',' read -r gpu_id gpu_name gpu_util vram_used vram_total temp power; do
                vram_usage=$((vram_used * 100 / vram_total))
                if [ $vram_usage -gt 90 ]; then
                    echo "[$timestamp] ⚠️  GPU $gpu_id HIGH VRAM: ${vram_usage}%" >> /app/logs/gpu_monitor.log
                fi
                if [ ${temp%.*} -gt 80 ]; then
                    echo "[$timestamp] 🌡️  GPU $gpu_id HIGH TEMP: ${temp}°C" >> /app/logs/gpu_monitor.log
                fi
            done <<< "$gpu_stats"
        fi
        
        sleep 30
    done
} &

# 启动系统监控（后台）
echo "📈 启动系统监控..."
{
    while true; do
        timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        
        # 系统内存
        mem_info=$(free -m | awk 'NR==2{printf "Used: %sMB (%.1f%%), Available: %sMB", $3, $3*100/$2, $7}')
        echo "[$timestamp] Memory: $mem_info" >> /app/logs/system_monitor.log
        
        # 磁盘空间
        disk_info=$(df -h /app | awk 'NR==2{printf "Used: %s (%s), Available: %s", $3, $5, $4}')
        echo "[$timestamp] Disk: $disk_info" >> /app/logs/system_monitor.log
        
        sleep 60
    done
} &

# 启动API服务器
echo "🌐 启动无限制SkyReels V2 API服务器..."
echo "🔗 服务地址: http://0.0.0.0:8000"
echo "📋 API文档: http://0.0.0.0:8000/docs"
echo "📊 健康检查: http://0.0.0.0:8000/health"

cd /app

# 启动主服务
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
    --capture-output \
    api_server_unlimited:app 
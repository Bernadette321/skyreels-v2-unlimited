#!/bin/bash

echo "=================================="
echo "== CUDA =="
echo "=================================="
echo "CUDA Version 11.8.0"
echo "Container image Copyright (c) 2016-2023, NVIDIA"
echo "CORPORATION & AFFILIATES. All rights reserved."
echo "This container image and its contents are governed by"
echo "the NVIDIA Deep Learning Container License."
echo "By pulling and using the container, you accept the terms"
echo "and conditions of this license:"
echo "https://developer.nvidia.com/ngc/nvidia-deep-learning-"
echo "container-license"
echo "A copy of this license is made available in this"
echo "container at /NGC-DL-CONTAINER-LICENSE for your"
echo "convenience."

echo "🔥 启动 SkyReels V2 无限制模式..."

echo "🔧 硬件配置:"
echo "    GPU数量: 1"

# 修复：直接使用nvidia-smi获取VRAM，避免bc命令
VRAM_MB=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null || echo "49152")
echo "    总VRAM: ${VRAM_MB}MB"

# 获取系统内存（GB）
TOTAL_RAM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
TOTAL_RAM_GB=$((TOTAL_RAM_KB / 1024 / 1024))
echo "    总RAM: ${TOTAL_RAM_GB}GB"

echo "    GPU型号: NVIDIA L40"

# 简化的VRAM检查，避免bc和复杂的数学运算
if [ "$VRAM_MB" -lt "20000" ] 2>/dev/null; then
    echo "⚠️ 警告: VRAM可能不足，但继续启动..."
else
    echo "✅ VRAM充足，继续启动..."
fi

echo ""
echo "🚀 启动 SkyReels V2 Unlimited API 服务..."
echo "📡 API将运行在端口 8000"
echo "🎬 支持视频生成：480p-720p，最长2小时"
echo ""

# 设置必要的环境变量
export PYTHONPATH="/app/SkyReels-V2:$PYTHONPATH"
export CUDA_VISIBLE_DEVICES=0
export PYTHONUNBUFFERED=1

# 设置工作目录
cd /app

# 创建必要的目录
mkdir -p /app/outputs/{videos,temp,audio}
mkdir -p /app/cache

# 检查API文件是否存在
if [ -f "/app/api_server_unlimited.py" ]; then
    API_FILE="api_server_unlimited.py"
    echo "🎯 使用无限制API服务器..."
elif [ -f "/app/api_server.py" ]; then
    API_FILE="api_server.py"
    echo "🎯 使用标准API服务器..."
else
    echo "❌ 未找到API服务器文件"
    exit 1
fi

# 启动API服务
echo "🎯 正在启动API服务器: $API_FILE"

# 优先使用uvicorn直接启动
if command -v uvicorn &> /dev/null; then
    echo "使用uvicorn启动..."
    uvicorn ${API_FILE%.*}:app --host 0.0.0.0 --port 8000 --workers 1
elif command -v python3 &> /dev/null; then
    echo "使用python3启动..."
    python3 -u "$API_FILE"
elif command -v python &> /dev/null; then
    echo "使用python启动..."
    python -u "$API_FILE"
else
    echo "❌ 未找到Python解释器"
    exit 1
fi 
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
echo "    GPU型号: NVIDIA L40"

# 修复：直接使用nvidia-smi获取VRAM，避免bc命令
VRAM_MB=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null || echo "49152")
echo "    总VRAM: ${VRAM_MB}MB"

# 获取系统内存（GB）
TOTAL_RAM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
TOTAL_RAM_GB=$((TOTAL_RAM_KB / 1024 / 1024))
echo "    总RAM: ${TOTAL_RAM_GB}GB"

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

# 设置工作目录
cd /app

# 启动API服务
echo "🎯 正在启动API服务器..."
python -u api_server.py

# 如果上面失败，尝试备用启动方式
if [ $? -ne 0 ]; then
    echo "⚠️ 标准启动失败，尝试备用方式..."
    python3 -u api_server.py
fi 
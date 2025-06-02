#!/bin/bash
# 手动修复RunPod容器的命令

echo "🔧 手动修复SkyReels V2容器"

# 如果能通过SSH连接到容器，运行这些命令：

# 1. 进入容器
echo "1. 尝试进入容器..."
docker exec -it $(docker ps -q) /bin/bash

# 2. 安装bc命令（如果需要）
echo "2. 安装bc命令..."
apt update && apt install -y bc

# 3. 修复启动脚本
echo "3. 备份并修复启动脚本..."
cd /app
cp start_unlimited.sh start_unlimited.sh.backup

# 4. 创建修复版启动脚本
cat > /app/start_unlimited_fixed.sh << 'EOF'
#!/bin/bash
echo "🔥 启动 SkyReels V2 无限制模式..."
echo "🔧 硬件配置:"
echo "    GPU数量: 1"
echo "    GPU型号: NVIDIA L40"

# 获取VRAM（避免bc命令）
VRAM_MB=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null || echo "49152")
echo "    总VRAM: ${VRAM_MB}MB"

# 获取RAM
TOTAL_RAM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
TOTAL_RAM_GB=$((TOTAL_RAM_KB / 1024 / 1024))
echo "    总RAM: ${TOTAL_RAM_GB}GB"

echo "✅ 硬件检查完成，启动API服务..."
cd /app
python -u api_server.py
EOF

# 5. 设置权限并运行
chmod +x /app/start_unlimited_fixed.sh

# 6. 停止原进程并启动修复版
pkill -f api_server.py
pkill -f start_unlimited.sh

# 7. 启动修复版
echo "🚀 启动修复版API..."
/app/start_unlimited_fixed.sh 
#!/bin/bash
# SkyReels V2 Real Implementation Fix Script
# 在RunPod上部署真正的SkyReels-V2

echo "🔧 开始修复SkyReels V2部署..."

# 1. 创建必要目录
echo "📁 创建目录结构..."
mkdir -p /app/models
mkdir -p /app/outputs/videos
mkdir -p /app/outputs/audio
mkdir -p /app/logs

# 2. 下载官方SkyReels-V2代码
echo "📥 下载官方SkyReels-V2代码..."
cd /app
if [ ! -d "SkyReels-V2" ]; then
    git clone https://github.com/SkyworkAI/SkyReels-V2.git
    echo "✅ SkyReels-V2代码下载完成"
else
    echo "✅ SkyReels-V2代码已存在"
fi

# 3. 安装依赖
echo "📦 安装Python依赖..."
cd /app/SkyReels-V2
pip install -r requirements.txt
pip install huggingface-hub fastapi uvicorn python-multipart

# 4. 下载模型文件
echo "🤖 下载SkyReels-V2模型..."
python3 << 'EOF'
from huggingface_hub import snapshot_download
import os

models = [
    'SkyworkAI/SkyReels-V2-DF-14B-720P',
    'SkyworkAI/SkyReels-V2-I2V-14B-720P'
]

for model in models:
    model_name = model.split('/')[-1]
    local_dir = f'/app/models/{model_name}'
    
    if not os.path.exists(local_dir):
        print(f"📥 下载模型: {model}")
        try:
            snapshot_download(model, local_dir=local_dir)
            print(f"✅ 模型下载完成: {model_name}")
        except Exception as e:
            print(f"❌ 模型下载失败 {model_name}: {e}")
    else:
        print(f"✅ 模型已存在: {model_name}")
EOF

# 5. 复制新的API服务器
echo "🔄 更新API服务器..."
cp /app/api_server_real.py /app/api_server_unlimited.py

# 6. 停止旧服务
echo "🛑 停止旧服务..."
pkill -f api_server || true
pkill -f uvicorn || true
sleep 2

# 7. 启动新服务
echo "🚀 启动真正的SkyReels V2 API..."
cd /app
nohup python3 api_server_real.py > /app/logs/api_server.log 2>&1 &

# 8. 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 9. 检查服务状态
echo "🔍 检查服务状态..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ SkyReels V2 Real API启动成功！"
    curl -s http://localhost:8000/health | python3 -m json.tool
else
    echo "❌ API启动失败，检查日志:"
    tail -20 /app/logs/api_server.log
    exit 1
fi

echo "🎉 SkyReels V2真正实现部署完成！"
echo "📝 使用方法:"
echo "   - 健康检查: curl http://localhost:8000/health"
echo "   - API文档: http://localhost:8000/docs"
echo "   - 日志文件: /app/logs/api_server.log" 
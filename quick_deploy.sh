#!/bin/bash

# SkyReels V2 快速部署脚本
# 使用方法: ./quick_deploy.sh [DOCKERHUB_USERNAME]

set -e

echo "🚀 SkyReels V2 快速部署脚本"
echo "=================================="

# 检查参数
if [ $# -eq 0 ]; then
    echo "❌ 错误: 请提供Docker Hub用户名"
    echo "使用方法: ./quick_deploy.sh your-dockerhub-username"
    exit 1
fi

DOCKERHUB_USERNAME=$1
IMAGE_NAME="skyreels-v2"
IMAGE_TAG="latest"
FULL_IMAGE_NAME="${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${IMAGE_TAG}"

echo "📋 部署配置:"
echo "   Docker Hub用户: $DOCKERHUB_USERNAME"
echo "   镜像名称: $FULL_IMAGE_NAME"
echo ""

# 步骤1: 检查Docker镜像
echo "🔍 步骤1: 检查本地Docker镜像..."
if docker images | grep -q "skyreels-v2-720p"; then
    echo "✅ 找到本地镜像: skyreels-v2-720p:latest"
else
    echo "❌ 未找到本地镜像，请先运行 ./build.sh"
    exit 1
fi

# 步骤2: 标记镜像
echo ""
echo "🏷️  步骤2: 标记镜像用于上传..."
docker tag skyreels-v2-720p:latest $FULL_IMAGE_NAME
echo "✅ 镜像已标记为: $FULL_IMAGE_NAME"

# 步骤3: 检查Docker Hub登录状态
echo ""
echo "🔐 步骤3: 检查Docker Hub登录..."
if docker info | grep -q "Username:"; then
    echo "✅ 已登录Docker Hub"
else
    echo "⚠️  需要登录Docker Hub"
    docker login
fi

# 步骤4: 推送镜像
echo ""
echo "📤 步骤4: 推送镜像到Docker Hub..."
echo "   注意: 这可能需要20-40分钟，镜像大小约18.5GB"
echo ""
read -p "是否继续推送镜像? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📤 开始推送镜像..."
    docker push $FULL_IMAGE_NAME
    echo "✅ 镜像推送完成!"
else
    echo "⏭️  跳过镜像推送"
fi

# 步骤5: 生成RunPod配置
echo ""
echo "🐳 步骤5: 生成RunPod部署配置..."

cat > runpod_config.yaml << EOF
# RunPod部署配置
# 复制以下内容到RunPod控制台

Docker镜像: $FULL_IMAGE_NAME
端口映射: 8000:8000
启动命令: /app/start.sh

环境变量:
  CUDA_VISIBLE_DEVICES: "0"
  PYTHONPATH: "/app/SkyReels-V2"
  HF_HOME: "/app/cache"
  TRANSFORMERS_CACHE: "/app/cache"
  TORCH_HOME: "/app/cache"
  OMP_NUM_THREADS: "8"

推荐GPU配置:
  - NVIDIA RTX 4090 (24GB VRAM)
  - 32GB+ RAM
  - 100GB+ NVMe SSD

卷挂载 (可选):
  - /workspace/models:/app/models
  - /workspace/results:/app/results
  - /workspace/cache:/app/cache
EOF

echo "✅ RunPod配置已保存到: runpod_config.yaml"

# 步骤6: 生成测试脚本
echo ""
echo "🧪 步骤6: 生成API测试脚本..."

cat > test_runpod_api.sh << 'EOF'
#!/bin/bash

# RunPod API测试脚本
# 使用方法: ./test_runpod_api.sh https://your-runpod-instance:8000

if [ $# -eq 0 ]; then
    echo "使用方法: ./test_runpod_api.sh https://your-runpod-instance:8000"
    exit 1
fi

API_ENDPOINT=$1

echo "🔍 测试RunPod API: $API_ENDPOINT"
echo "=================================="

echo "1. 健康检查..."
curl -s -X GET "$API_ENDPOINT/health" | jq .

echo -e "\n2. 启动短视频生成测试..."
RESPONSE=$(curl -s -X POST "$API_ENDPOINT/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A beautiful sunset over the ocean with gentle waves",
    "duration": 30,
    "resolution": "720p"
  }')

echo $RESPONSE | jq .
TASK_ID=$(echo $RESPONSE | jq -r '.task_id')

if [ "$TASK_ID" != "null" ]; then
    echo -e "\n3. 监控生成状态 (Task ID: $TASK_ID)..."
    for i in {1..20}; do
        sleep 30
        STATUS=$(curl -s -X GET "$API_ENDPOINT/status/$TASK_ID" | jq -r '.status')
        PROGRESS=$(curl -s -X GET "$API_ENDPOINT/status/$TASK_ID" | jq -r '.progress')
        echo "   检查 $i: 状态=$STATUS, 进度=$PROGRESS"
        
        if [ "$STATUS" = "completed" ]; then
            echo "✅ 视频生成完成!"
            echo "📥 下载地址: $API_ENDPOINT/download/$TASK_ID"
            break
        elif [ "$STATUS" = "failed" ]; then
            echo "❌ 视频生成失败"
            break
        fi
    done
else
    echo "❌ 生成请求失败"
fi
EOF

chmod +x test_runpod_api.sh
echo "✅ API测试脚本已保存到: test_runpod_api.sh"

# 步骤7: 更新n8n工作流配置
echo ""
echo "🔄 步骤7: 生成n8n配置更新脚本..."

cat > update_n8n_config.py << EOF
#!/usr/bin/env python3

# n8n工作流配置更新脚本
# 使用方法: python3 update_n8n_config.py https://your-runpod-instance:8000

import json
import sys

if len(sys.argv) != 2:
    print("使用方法: python3 update_n8n_config.py https://your-runpod-instance:8000")
    sys.exit(1)

runpod_endpoint = sys.argv[1]

# 读取工作流文件
with open('SkyReels_V2_Docker_API_Workflow.json', 'r', encoding='utf-8') as f:
    workflow = json.load(f)

# 更新API端点
for node in workflow['nodes']:
    if node['name'] == '🎬 SkyReels V2 配置':
        for param in node['parameters']['values']['string']:
            if param['name'] == 'skyreelsEndpoint':
                param['value'] = runpod_endpoint
                break

# 保存更新的工作流
with open('SkyReels_V2_Docker_API_Workflow_Updated.json', 'w', encoding='utf-8') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print(f"✅ n8n工作流已更新: SkyReels_V2_Docker_API_Workflow_Updated.json")
print(f"   API端点已设置为: {runpod_endpoint}")
EOF

chmod +x update_n8n_config.py
echo "✅ n8n配置更新脚本已保存到: update_n8n_config.py"

# 步骤8: 显示下一步操作
echo ""
echo "🎯 部署完成! 下一步操作:"
echo "=================================="
echo ""
echo "1️⃣ 登录RunPod控制台 (https://runpod.io)"
echo "   - 选择 Deploy -> Pods"
echo "   - 使用配置文件: runpod_config.yaml"
echo ""
echo "2️⃣ 获取RunPod实例地址后，测试API:"
echo "   ./test_runpod_api.sh https://your-runpod-instance:8000"
echo ""
echo "3️⃣ 更新n8n工作流配置:"
echo "   python3 update_n8n_config.py https://your-runpod-instance:8000"
echo ""
echo "4️⃣ 导入更新的工作流到n8n:"
echo "   SkyReels_V2_Docker_API_Workflow_Updated.json"
echo ""
echo "📚 详细部署指南请查看: 部署检查清单.md"
echo ""
echo "🔥 镜像信息:"
echo "   Docker Hub: $FULL_IMAGE_NAME"
echo "   大小: ~18.5GB"
echo "   CUDA版本: 12.9.0"
echo "   支持分辨率: 720P"
echo "   最大时长: 720秒 (12分钟)"
echo ""
echo "🚀 部署成功! 准备在RunPod上享受最强AI视频生成性能!" 
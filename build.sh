#!/bin/bash

set -e

# 配置变量
IMAGE_NAME="skyreels-v2-720p"
TAG=${1:-"latest"}
REGISTRY=${REGISTRY:-""}  # 如果要推送到私有仓库，设置这个变量
FULL_IMAGE_NAME="${REGISTRY}${IMAGE_NAME}:${TAG}"

echo "🏗️  Building SkyReels V2 Docker Image..."
echo "   Image: ${FULL_IMAGE_NAME}"
echo "   Timestamp: $(date)"

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    exit 1
fi

# 检查NVIDIA Docker运行时
if ! docker info | grep -q nvidia; then
    echo "⚠️  NVIDIA Docker runtime not detected"
    echo "   The image will still build but GPU support may not work"
fi

# 创建必要的目录
mkdir -p models results cache logs

# 构建镜像
echo "🔨 Building Docker image..."
docker build \
    --tag "${FULL_IMAGE_NAME}" \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    --progress=plain \
    .

# 检查构建结果
if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully!"
    echo "   Image size:"
    docker images "${FULL_IMAGE_NAME}" --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}"
    
    # 显示使用说明
    echo ""
    echo "🚀 Usage:"
    echo "   # Run with Docker Compose (推荐)"
    echo "   docker-compose up -d"
    echo ""
    echo "   # Run directly with Docker"
    echo "   docker run -d --gpus all -p 8000:8000 \\"
    echo "     -v \$(pwd)/models:/app/models \\"
    echo "     -v \$(pwd)/results:/app/results \\"
    echo "     --name skyreels-v2 ${FULL_IMAGE_NAME}"
    echo ""
    echo "   # Test the API"
    echo "   curl http://localhost:8000/health"
    echo ""
    
    # 可选：推送到仓库
    if [ -n "${REGISTRY}" ] && [ "${PUSH_IMAGE}" = "true" ]; then
        echo "📤 Pushing image to registry..."
        docker push "${FULL_IMAGE_NAME}"
    fi
    
else
    echo "❌ Docker build failed!"
    exit 1
fi

# 清理构建缓存（可选）
if [ "${CLEANUP}" = "true" ]; then
    echo "🧹 Cleaning up build cache..."
    docker builder prune -f
fi

echo "🎉 Build completed successfully!" 
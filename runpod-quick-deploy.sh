#!/bin/bash

# SkyReels V2 Unlimited - RunPod快速部署脚本
# 使用GitHub Actions构建的Docker镜像

set -e

echo "🚀 SkyReels V2 Unlimited - RunPod快速部署"
echo "============================================"

# 配置变量
GITHUB_USERNAME="your-github-username"  # 替换为您的GitHub用户名
IMAGE_URL="ghcr.io/${GITHUB_USERNAME}/skyreels-v2-unlimited:latest"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 检查GPU环境
check_gpu() {
    log_info "检查GPU环境..."
    
    if ! nvidia-smi > /dev/null 2>&1; then
        log_error "未检测到NVIDIA GPU"
        exit 1
    fi
    
    GPU_MEMORY=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -n1)
    GPU_MEMORY_GB=$((GPU_MEMORY / 1024))
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -n1)
    
    log_success "检测到GPU: ${GPU_NAME}"
    log_success "GPU内存: ${GPU_MEMORY_GB}GB"
    
    if [ $GPU_MEMORY_GB -lt 40 ]; then
        log_warning "建议使用40GB+显存的GPU以获得最佳性能"
    fi
}

# 创建必要目录
setup_directories() {
    log_info "创建工作目录..."
    
    mkdir -p /workspace/{outputs,cache,logs}/{videos,temp,audio,models,diffusers,transformers}
    chmod -R 755 /workspace/{outputs,cache,logs}
    
    log_success "目录创建完成"
}

# 停止已存在的容器
cleanup_existing() {
    log_info "清理已存在的容器..."
    
    if docker ps -a | grep -q skyreels-unlimited; then
        docker stop skyreels-unlimited > /dev/null 2>&1 || true
        docker rm skyreels-unlimited > /dev/null 2>&1 || true
        log_success "已清理旧容器"
    fi
}

# 拉取最新镜像
pull_image() {
    log_info "拉取最新Docker镜像..."
    log_info "镜像地址: ${IMAGE_URL}"
    
    # GitHub Container Registry需要登录（公开镜像可以跳过）
    if ! docker pull "${IMAGE_URL}"; then
        log_error "镜像拉取失败，请检查："
        echo "1. GitHub用户名是否正确"
        echo "2. 镜像是否已构建并推送"
        echo "3. 是否需要GitHub认证"
        exit 1
    fi
    
    log_success "镜像拉取成功"
}

# 启动容器
start_container() {
    log_info "启动SkyReels V2无限制容器..."
    
    docker run -d \
        --name skyreels-unlimited \
        --gpus all \
        --restart unless-stopped \
        -p 8000:8000 \
        -v /workspace/outputs:/app/outputs \
        -v /workspace/cache:/app/cache \
        -v /workspace/logs:/app/logs \
        -e SKYREELS_UNLIMITED_MODE=true \
        -e SKYREELS_MAX_DURATION=7200 \
        -e SKYREELS_ENABLE_4K=true \
        -e SKYREELS_HIGH_QUALITY=true \
        -e CUDA_VISIBLE_DEVICES=0 \
        -e PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:4096 \
        -e OMP_NUM_THREADS=16 \
        -e MKL_NUM_THREADS=16 \
        --shm-size=2g \
        "${IMAGE_URL}"
    
    if [ $? -eq 0 ]; then
        log_success "容器启动成功"
    else
        log_error "容器启动失败"
        exit 1
    fi
}

# 等待服务就绪
wait_for_service() {
    log_info "等待服务启动（最多120秒）..."
    
    for i in {1..24}; do
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            log_success "服务已就绪"
            return 0
        fi
        
        if [ $i -eq 24 ]; then
            log_error "服务启动超时"
            docker logs skyreels-unlimited --tail 50
            exit 1
        fi
        
        echo -n "."
        sleep 5
    done
}

# 显示部署信息
show_deployment_info() {
    echo
    log_success "🎉 SkyReels V2 Unlimited部署成功！"
    echo
    echo "📋 服务信息:"
    echo "  🌐 API地址: http://localhost:8000"
    echo "  📖 API文档: http://localhost:8000/docs"
    echo "  💡 健康检查: http://localhost:8000/health"
    echo "  📊 系统状态: http://localhost:8000/system/stats"
    echo
    echo "🎮 GPU配置:"
    echo "  💾 GPU内存: ${GPU_MEMORY_GB}GB"
    echo "  🎯 GPU型号: ${GPU_NAME}"
    echo "  🔥 支持4K: 是"
    echo "  ⏱️  最大时长: 2小时+"
    echo
    echo "📁 目录结构:"
    echo "  📤 输出目录: /workspace/outputs"
    echo "  💾 缓存目录: /workspace/cache"
    echo "  📋 日志目录: /workspace/logs"
    echo
    echo "🧪 测试命令:"
    echo '  curl -X POST "http://localhost:8000/generate" \'
    echo '    -H "Content-Type: application/json" \'
    echo '    -d "{\"prompt\": \"A beautiful sunset\", \"duration\": 60}"'
    echo
    echo "📊 查看日志:"
    echo "  docker logs -f skyreels-unlimited"
    echo
}

# 主函数
main() {
    # 检查是否在RunPod环境
    if [ ! -d "/workspace" ]; then
        log_warning "似乎不在RunPod环境中，将使用当前目录"
        mkdir -p {outputs,cache,logs}
    fi
    
    check_gpu
    setup_directories
    cleanup_existing
    pull_image
    start_container
    wait_for_service
    show_deployment_info
    
    log_success "部署完成！开始您的无限制AI视频创作之旅！"
}

# 执行部署
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 
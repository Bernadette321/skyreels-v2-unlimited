#!/bin/bash

# SkyReels V2 无限制版本一键部署脚本
# 支持RunPod和本地高性能GPU环境

set -e

echo "🚀 SkyReels V2 无限制版本部署开始..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查系统要求
check_system() {
    log_info "检查系统要求..."
    
    # 检查NVIDIA GPU
    if ! nvidia-smi > /dev/null 2>&1; then
        log_error "未检测到NVIDIA GPU或驱动未安装"
        exit 1
    fi
    
    # 检测GPU内存
    GPU_MEMORY=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -n1)
    GPU_MEMORY_GB=$((GPU_MEMORY / 1024))
    
    log_info "检测到GPU内存: ${GPU_MEMORY_GB}GB"
    
    if [ $GPU_MEMORY_GB -lt 20 ]; then
        log_error "无限制模式至少需要20GB GPU内存，当前只有${GPU_MEMORY_GB}GB"
        exit 1
    elif [ $GPU_MEMORY_GB -lt 40 ]; then
        log_warning "当前GPU内存${GPU_MEMORY_GB}GB，建议使用40GB+以获得最佳性能"
        export SKYREELS_MODE="standard"
    elif [ $GPU_MEMORY_GB -lt 70 ]; then
        log_success "GPU内存充足，启用扩展模式"
        export SKYREELS_MODE="extended"
    else
        log_success "检测到高端GPU，启用无限制模式"
        export SKYREELS_MODE="unlimited"
    fi
    
    # 检查Docker
    if ! docker --version > /dev/null 2>&1; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! docker compose version > /dev/null 2>&1; then
        log_warning "Docker Compose插件未安装，将使用docker命令部署"
        USE_COMPOSE=false
    else
        USE_COMPOSE=true
    fi
    
    # 检查nvidia-docker
    if ! docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi > /dev/null 2>&1; then
        log_error "nvidia-docker未正确配置"
        exit 1
    fi
    
    log_success "系统检查通过"
}

# 设置环境变量
setup_environment() {
    log_info "设置无限制模式环境变量..."
    
    # 创建.env文件
    cat > .env << EOF
# SkyReels V2 无限制模式配置
SKYREELS_UNLIMITED_MODE=true
SKYREELS_MODE=${SKYREELS_MODE}
SKYREELS_MAX_RESOLUTION=1080p
SKYREELS_MAX_DURATION=7200
SKYREELS_ENABLE_4K=true
SKYREELS_HIGH_QUALITY=true

# GPU配置
CUDA_VISIBLE_DEVICES=0
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:4096

# 性能优化
OMP_NUM_THREADS=16
MKL_NUM_THREADS=16

# 缓存目录
HF_HOME=/app/cache
TRANSFORMERS_CACHE=/app/cache
TORCH_HOME=/app/cache
EOF
    
    log_success "环境变量配置完成"
}

# 创建目录结构
create_directories() {
    log_info "创建目录结构..."
    
    mkdir -p {outputs,cache,logs}/{videos,temp,audio,models,diffusers,transformers}
    chmod -R 755 {outputs,cache,logs}
    
    log_success "目录结构创建完成"
}

# 构建Docker镜像
build_image() {
    log_info "构建SkyReels V2无限制Docker镜像..."
    
    # 检查Dockerfile.unlimited是否存在
    if [ ! -f "Dockerfile.unlimited" ]; then
        log_error "Dockerfile.unlimited文件不存在"
        exit 1
    fi
    
    # 构建镜像
    docker build \
        -f Dockerfile.unlimited \
        -t skyreels-v2:unlimited \
        --build-arg GPU_MEMORY_GB=${GPU_MEMORY_GB} \
        --build-arg SKYREELS_MODE=${SKYREELS_MODE} \
        .
    
    if [ $? -eq 0 ]; then
        log_success "Docker镜像构建成功"
    else
        log_error "Docker镜像构建失败"
        exit 1
    fi
}

# 部署服务
deploy_service() {
    log_info "部署SkyReels V2无限制服务..."
    
    # 停止已存在的容器
    if docker ps -a | grep -q skyreels-unlimited; then
        log_warning "停止已存在的容器..."
        docker stop skyreels-unlimited > /dev/null 2>&1 || true
        docker rm skyreels-unlimited > /dev/null 2>&1 || true
    fi
    
    if [ "$USE_COMPOSE" = true ]; then
        # 使用Docker Compose部署
        log_info "使用Docker Compose部署..."
        docker compose -f docker-compose.unlimited.yml up -d
    else
        # 使用docker命令部署
        log_info "使用Docker命令部署..."
        docker run -d \
            --name skyreels-unlimited \
            --gpus all \
            --restart unless-stopped \
            -p 8000:8000 \
            -v "$(pwd)/outputs:/app/outputs" \
            -v "$(pwd)/cache:/app/cache" \
            -v "$(pwd)/logs:/app/logs" \
            --env-file .env \
            --shm-size=2g \
            skyreels-v2:unlimited
    fi
    
    if [ $? -eq 0 ]; then
        log_success "服务部署成功"
    else
        log_error "服务部署失败"
        exit 1
    fi
}

# 验证部署
verify_deployment() {
    log_info "验证部署状态..."
    
    # 等待服务启动
    log_info "等待服务启动（最多120秒）..."
    for i in {1..24}; do
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            log_success "服务健康检查通过"
            break
        fi
        
        if [ $i -eq 24 ]; then
            log_error "服务启动超时"
            docker logs skyreels-unlimited --tail 50
            exit 1
        fi
        
        echo -n "."
        sleep 5
    done
    echo
    
    # 获取服务信息
    log_info "获取服务信息..."
    SERVICE_INFO=$(curl -s http://localhost:8000/health 2>/dev/null || echo "{}")
    GPU_INFO=$(curl -s http://localhost:8000/models/info 2>/dev/null || echo "{}")
    
    echo
    log_success "🎉 SkyReels V2无限制版部署成功！"
    echo
    echo "📋 服务信息:"
    echo "  🌐 API地址: http://localhost:8000"
    echo "  📖 API文档: http://localhost:8000/docs"
    echo "  💡 健康检查: http://localhost:8000/health"
    echo "  📊 系统状态: http://localhost:8000/system/stats"
    echo
    echo "🎮 GPU配置:"
    echo "  💾 GPU内存: ${GPU_MEMORY_GB}GB"
    echo "  ⚡ 运行模式: ${SKYREELS_MODE}"
    echo "  🔥 支持4K: $([ "$SKYREELS_MODE" = "unlimited" ] && echo "是" || echo "否")"
    echo "  ⏱️  最大时长: 2小时+"
    echo
    echo "📁 目录结构:"
    echo "  📤 输出目录: $(pwd)/outputs"
    echo "  💾 缓存目录: $(pwd)/cache" 
    echo "  📋 日志目录: $(pwd)/logs"
    echo
}

# 显示使用说明
show_usage() {
    echo
    log_info "📝 使用说明:"
    echo
    echo "1. 测试API:"
    echo '   curl -X POST "http://localhost:8000/generate" \'
    echo '     -H "Content-Type: application/json" \'
    echo '     -d "{\"prompt\": \"A beautiful sunset\", \"duration\": 60}"'
    echo
    echo "2. 查看日志:"
    echo "   docker logs -f skyreels-unlimited"
    echo
    echo "3. 停止服务:"
    if [ "$USE_COMPOSE" = true ]; then
        echo "   docker compose -f docker-compose.unlimited.yml down"
    else
        echo "   docker stop skyreels-unlimited"
    fi
    echo
    echo "4. 重启服务:"
    if [ "$USE_COMPOSE" = true ]; then
        echo "   docker compose -f docker-compose.unlimited.yml restart"
    else
        echo "   docker restart skyreels-unlimited"
    fi
    echo
    echo "5. 清理缓存:"
    echo '   curl -X POST "http://localhost:8000/system/cleanup"'
    echo
}

# 主执行流程
main() {
    echo "🎬 SkyReels V2 无限制版本部署脚本"
    echo "======================================"
    echo
    
    check_system
    setup_environment
    create_directories
    build_image
    deploy_service
    verify_deployment
    show_usage
    
    echo "🚀 部署完成！您现在可以生成无限制长视频了！"
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 
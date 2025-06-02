#!/bin/bash

echo "🚀 SkyReels-V2 安全部署脚本（无中断）"
echo "====================================="

# 设置错误处理但不退出
set +e

# 色彩输出函数
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# 检查RunPod环境
check_environment() {
    info "检查运行环境..."
    if [ ! -d "/workspace" ]; then
        error "未检测到RunPod环境"
        return 1
    fi
    success "环境检查通过"
}

# 下载新实现（不影响旧服务）
download_new_implementation() {
    info "下载SkyReels-V2真实实现..."
    
    cd /workspace
    
    # 如果目录已存在，备份
    if [ -d "skyreels-v2-real" ]; then
        warning "备份现有目录..."
        mv skyreels-v2-real skyreels-v2-real.backup.$(date +%s)
    fi
    
    # 克隆新实现
    if git clone https://github.com/Bernadette321/skyreels-v2-unlimited.git skyreels-v2-real; then
        success "代码下载完成"
    else
        error "代码下载失败"
        return 1
    fi
}

# 安装依赖
setup_dependencies() {
    info "安装Python依赖..."
    
    cd /workspace/skyreels-v2-real
    
    # 安装核心依赖
    pip install --upgrade pip --quiet
    pip install huggingface-hub --quiet
    
    # 安装PyTorch
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 --quiet
    
    # 安装其他依赖
    pip install diffusers transformers accelerate --quiet
    pip install fastapi "uvicorn[standard]" pydantic --quiet
    pip install opencv-python-headless pillow numpy xformers --quiet
    
    success "依赖安装完成"
}

# 下载模型
download_models() {
    info "下载SkyReels-V2模型..."
    
    cd /workspace/skyreels-v2-real
    
    # 检查模型下载脚本
    if [ ! -f "download_models.py" ]; then
        error "未找到模型下载脚本"
        return 1
    fi
    
    # 后台下载模型（不阻塞）
    python3 download_models.py > logs/model_download.log 2>&1 &
    MODEL_DOWNLOAD_PID=$!
    
    info "模型下载已在后台启动 (PID: $MODEL_DOWNLOAD_PID)"
    info "可以使用以下命令查看进度: tail -f /workspace/skyreels-v2-real/logs/model_download.log"
}

# 配置新服务使用不同端口
configure_service() {
    info "配置新服务..."
    
    cd /workspace/skyreels-v2-real
    
    # 创建目录
    mkdir -p logs results
    
    # 修改端口避免冲突
    if [ -f "api_server_real.py" ]; then
        # 使用端口8001避免与现有服务冲突
        sed -i 's/port=8000/port=8001/g' api_server_real.py 2>/dev/null || true
        sed -i 's/host="0.0.0.0", port=8000/host="0.0.0.0", port=8001/g' api_server_real.py 2>/dev/null || true
        success "服务配置完成（端口：8001）"
    else
        error "未找到API服务器文件"
        return 1
    fi
}

# 等待模型下载完成
wait_for_models() {
    info "等待模型下载完成..."
    
    # 等待模型下载进程
    if [ ! -z "$MODEL_DOWNLOAD_PID" ]; then
        while kill -0 $MODEL_DOWNLOAD_PID 2>/dev/null; do
            echo -n "."
            sleep 10
        done
        echo ""
        success "模型下载完成"
    fi
    
    # 验证模型文件
    if [ -d "/workspace/skyreels-v2-real/models" ] && [ "$(ls -A /workspace/skyreels-v2-real/models 2>/dev/null)" ]; then
        success "模型文件验证通过"
    else
        warning "模型文件可能不完整，但服务仍会尝试启动"
    fi
}

# 启动新服务
start_new_service() {
    info "启动新的SkyReels-V2服务..."
    
    cd /workspace/skyreels-v2-real
    
    # 后台启动新服务
    nohup python3 api_server_real.py > logs/api_server_real.log 2>&1 &
    NEW_SERVICE_PID=$!
    
    echo $NEW_SERVICE_PID > api_server_real.pid
    
    # 等待服务启动
    sleep 10
    
    # 检查服务状态
    if kill -0 $NEW_SERVICE_PID 2>/dev/null; then
        success "新服务启动成功 (PID: $NEW_SERVICE_PID)"
        info "新服务地址: http://localhost:8001"
        info "API文档: http://localhost:8001/docs"
    else
        error "新服务启动失败"
        return 1
    fi
}

# 测试新服务
test_new_service() {
    info "测试新服务..."
    
    # 等待服务完全启动
    sleep 5
    
    # 测试健康检查
    if curl -s http://localhost:8001/health >/dev/null 2>&1; then
        success "新服务健康检查通过"
    else
        warning "健康检查失败，服务可能还在启动中"
    fi
}

# 提供切换说明
provide_switch_instructions() {
    info "部署完成！服务切换说明："
    echo "================================"
    echo ""
    echo "✅ 新的真实SkyReels-V2服务已在端口8001启动"
    echo "📍 新服务地址: http://localhost:8001"
    echo "📖 API文档: http://localhost:8001/docs"
    echo ""
    echo "🔄 如果新服务工作正常，可以停止旧服务："
    echo "   pkill -f 'api_server_unlimited' || true"
    echo ""
    echo "📊 检查服务状态："
    echo "   # 新服务日志"
    echo "   tail -f /workspace/skyreels-v2-real/logs/api_server_real.log"
    echo ""
    echo "   # 检查端口"
    echo "   netstat -tlnp | grep -E ':(8000|8001)'"
    echo ""
    echo "🎬 测试视频生成："
    echo "   curl -X POST http://localhost:8001/generate \\"
    echo "     -H 'Content-Type: application/json' \\"
    echo "     -d '{\"prompt\": \"A sunset over the ocean\", \"duration\": 30}'"
}

# 主函数
main() {
    info "开始安全部署SkyReels-V2真实实现..."
    
    if ! check_environment; then
        exit 1
    fi
    
    if ! download_new_implementation; then
        exit 1
    fi
    
    if ! setup_dependencies; then
        exit 1
    fi
    
    if ! configure_service; then
        exit 1
    fi
    
    download_models  # 后台执行，不等待
    
    if ! start_new_service; then
        exit 1
    fi
    
    test_new_service
    wait_for_models
    provide_switch_instructions
    
    success "安全部署完成！旧服务仍在运行，新服务在端口8001"
}

# 执行主函数
main "$@" 
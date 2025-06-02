#!/bin/bash

echo "🚀 SkyReels-V2 真实实现 - RunPod部署脚本"
echo "========================================"

# 设置错误处理
set -e

# 色彩输出函数
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
    exit 1
}

# 检查是否在RunPod环境中
check_runpod_environment() {
    info "检查RunPod环境..."
    
    if [ ! -d "/workspace" ]; then
        error "未检测到RunPod环境，请在RunPod Pod中运行此脚本"
    fi
    
    success "RunPod环境检测通过"
}

# 停止旧服务
stop_old_services() {
    info "停止旧的SkyReels服务..."
    
    # 停止所有Python API服务器
    pkill -f "api_server" || true
    pkill -f "python.*api" || true
    
    # 等待进程完全停止
    sleep 3
    
    success "旧服务已停止"
}

# 下载新的实现文件
download_implementation_files() {
    info "下载SkyReels-V2真实实现文件..."
    
    cd /workspace
    
    # 如果存在旧的skyreels目录，备份它
    if [ -d "skyreels-v2-real" ]; then
        warning "发现旧的实现目录，正在备份..."
        mv skyreels-v2-real skyreels-v2-real.backup.$(date +%s)
    fi
    
    # 克隆真实实现
    git clone https://github.com/Bernadette321/skyreels-v2-unlimited.git skyreels-v2-real
    cd skyreels-v2-real
    
    success "实现文件下载完成"
}

# 安装依赖
install_dependencies() {
    info "安装Python依赖..."
    
    cd /workspace/skyreels-v2-real
    
    # 更新pip
    pip install --upgrade pip
    
    # 安装huggingface-hub（用于下载模型）
    pip install huggingface-hub
    
    # 安装PyTorch（支持CUDA）
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
    
    # 安装Diffusers和相关库
    pip install diffusers transformers accelerate
    
    # 安装其他必需的依赖
    pip install fastapi uvicorn[standard] pydantic
    pip install opencv-python-headless pillow numpy
    pip install xformers
    
    success "依赖安装完成"
}

# 下载SkyReels-V2模型
download_models() {
    info "下载SkyReels-V2模型..."
    
    cd /workspace/skyreels-v2-real
    
    # 运行修复后的模型下载脚本
    if [ -f "download_models.py" ]; then
        python3 download_models.py
    else
        error "未找到模型下载脚本"
    fi
    
    success "模型下载完成"
}

# 设置环境变量
setup_environment() {
    info "设置环境变量..."
    
    export CUDA_VISIBLE_DEVICES=0
    export PYTHONPATH="/workspace/skyreels-v2-real:$PYTHONPATH"
    export HF_HOME="/workspace/.cache/huggingface"
    
    # 创建必要目录
    mkdir -p /workspace/.cache/huggingface
    mkdir -p /workspace/skyreels-v2-real/results
    mkdir -p /workspace/skyreels-v2-real/logs
    
    success "环境设置完成"
}

# 验证GPU可用性
check_gpu() {
    info "检查GPU可用性..."
    
    if ! command -v nvidia-smi &> /dev/null; then
        error "未找到nvidia-smi，GPU可能不可用"
    fi
    
    # 显示GPU信息
    nvidia-smi
    
    # 测试PyTorch CUDA支持
    python3 -c "
import torch
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA device count: {torch.cuda.device_count()}')
    print(f'Current device: {torch.cuda.current_device()}')
    print(f'Device name: {torch.cuda.get_device_name()}')
else:
    print('警告: CUDA不可用，将使用CPU（速度会很慢）')
"
    
    success "GPU检查完成"
}

# 启动SkyReels-V2真实服务
start_real_service() {
    info "启动SkyReels-V2真实服务..."
    
    cd /workspace/skyreels-v2-real
    
    # 检查API服务器文件是否存在
    if [ ! -f "api_server_real.py" ]; then
        error "未找到api_server_real.py文件"
    fi
    
    # 后台启动API服务器
    nohup python3 api_server_real.py > logs/api_server.log 2>&1 &
    
    # 记录进程ID
    echo $! > api_server.pid
    
    # 等待服务启动
    info "等待服务启动..."
    sleep 10
    
    # 检查服务是否正常运行
    if ps -p $(cat api_server.pid) > /dev/null; then
        success "SkyReels-V2真实服务启动成功！"
        info "服务运行在: http://localhost:8000"
        info "API文档: http://localhost:8000/docs"
        info "健康检查: http://localhost:8000/health"
    else
        error "服务启动失败，请检查日志: logs/api_server.log"
    fi
}

# 显示服务状态
show_service_status() {
    info "服务状态信息"
    echo "===================="
    
    # 显示进程状态
    if [ -f "/workspace/skyreels-v2-real/api_server.pid" ]; then
        local pid=$(cat /workspace/skyreels-v2-real/api_server.pid)
        if ps -p $pid > /dev/null; then
            success "API服务器运行中 (PID: $pid)"
        else
            warning "API服务器未运行"
        fi
    else
        warning "未找到API服务器PID文件"
    fi
    
    # 显示端口监听状态
    info "端口监听状态:"
    netstat -tlnp | grep :8000 || warning "端口8000未监听"
    
    # 显示最近的日志
    if [ -f "/workspace/skyreels-v2-real/logs/api_server.log" ]; then
        info "最近的服务日志:"
        tail -10 /workspace/skyreels-v2-real/logs/api_server.log
    fi
}

# 运行测试
run_test() {
    info "运行API测试..."
    
    # 等待服务完全启动
    sleep 5
    
    # 测试健康检查端点
    if curl -s http://localhost:8000/health >/dev/null; then
        success "健康检查通过"
    else
        warning "健康检查失败，服务可能还在启动中"
    fi
    
    info "如果要进行视频生成测试，请访问: http://localhost:8000/docs"
}

# 主函数
main() {
    info "开始部署SkyReels-V2真实实现..."
    
    check_runpod_environment
    stop_old_services
    download_implementation_files
    install_dependencies
    setup_environment
    check_gpu
    download_models
    start_real_service
    show_service_status
    run_test
    
    echo ""
    echo "🎉 SkyReels-V2真实实现部署完成！"
    echo ""
    echo "📋 使用说明:"
    echo "  • API文档: http://localhost:8000/docs"
    echo "  • 健康检查: http://localhost:8000/health"
    echo "  • 日志文件: /workspace/skyreels-v2-real/logs/api_server.log"
    echo ""
    echo "🔧 管理命令:"
    echo "  • 停止服务: pkill -f api_server_real"
    echo "  • 查看日志: tail -f /workspace/skyreels-v2-real/logs/api_server.log"
    echo "  • 重启服务: cd /workspace/skyreels-v2-real && python3 api_server_real.py"
    echo ""
    echo "💡 提示: 如果遇到问题，请检查日志文件获取详细错误信息"
}

# 捕获中断信号
trap 'error "部署过程被中断"' INT TERM

# 执行主函数
main "$@" 
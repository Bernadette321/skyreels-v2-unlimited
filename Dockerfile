# 使用NVIDIA CUDA基础镜像，支持PyTorch
FROM nvidia/cuda:12.9.0-cudnn-devel-ubuntu22.04

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=${CUDA_HOME}/bin:${PATH}
ENV LD_LIBRARY_PATH=${CUDA_HOME}/lib64:${LD_LIBRARY_PATH}

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    git \
    wget \
    curl \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 创建工作目录
WORKDIR /app

# 复制项目文件
COPY SkyReels-V2/ ./SkyReels-V2/
COPY api_server.py ./
COPY requirements_docker.txt ./

# 安装Python依赖
RUN pip3 install --no-cache-dir -r requirements_docker.txt

# 设置Python路径
ENV PYTHONPATH=/app/SkyReels-V2:$PYTHONPATH

# 创建模型存储目录
RUN mkdir -p /app/models /app/results /app/cache

# 设置模型缓存目录
ENV HF_HOME=/app/cache
ENV TRANSFORMERS_CACHE=/app/cache
ENV TORCH_HOME=/app/cache

# 暴露端口
EXPOSE 8000

# 创建启动脚本
COPY start.sh ./
RUN chmod +x start.sh

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 设置启动命令
CMD ["./start.sh"] 
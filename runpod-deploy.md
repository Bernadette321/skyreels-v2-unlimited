# RunPod SkyReels V2 无限制部署指南

## 🎯 目标
在RunPod上部署SkyReels V2无限制版本，支持任意时长和分辨率的视频生成。

---

## 🔥 推荐RunPod配置

### 高性能配置 (推荐)
```yaml
配置规格:
🚀 GPU: NVIDIA A100 80GB 或 H100 80GB
🚀 vCPU: 32+ cores
🚀 RAM: 128GB+
🚀 存储: 500GB+ NVMe SSD
🚀 网络: 高速连接

预期性能:
✅ 1080P 60分钟: ~60-90分钟生成
✅ 720P 60分钟: ~35-50分钟生成
✅ 支持4K短视频
✅ 无时长限制

成本: ~$3-5/小时
```

### 性价比配置
```yaml
配置规格:
💪 GPU: NVIDIA A100 40GB
💪 vCPU: 24+ cores
💪 RAM: 64GB+
💪 存储: 300GB+ SSD

性能表现:
✅ 1080P 30分钟: ~45-60分钟生成
✅ 720P 60分钟: ~50-70分钟生成
✅ 稳定可靠

成本: ~$2-3/小时
```

---

## 📋 部署步骤

### 1. 创建RunPod实例

```bash
# 登录RunPod控制台
# 选择 "Deploy" -> "Pods"

# 推荐配置筛选:
GPU: A100 80GB SXM 或 H100 80GB
vCPU: 32+ cores
RAM: 128GB+
Storage: 500GB+ NVMe
```

### 2. Docker镜像配置

#### 方式1: 使用预构建镜像 (推荐)
```yaml
Docker配置:
镜像: skyreels/skyreels-v2:unlimited
端口映射: 8000:8000
启动命令: /app/start_unlimited.sh
```

#### 方式2: 现场构建
```yaml
Docker配置:
镜像: nvidia/cuda:12.1-devel-ubuntu22.04
端口映射: 8000:8000
启动命令: /bin/bash
```

### 3. 环境变量设置

```bash
# 基础配置
SKYREELS_UNLIMITED_MODE=true
SKYREELS_MAX_RESOLUTION=1080p
SKYREELS_MAX_DURATION=7200  # 2小时，可调整更大
SKYREELS_ENABLE_4K=true
SKYREELS_HIGH_QUALITY=true

# GPU优化
CUDA_VISIBLE_DEVICES=0
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:4096
OMP_NUM_THREADS=16
MKL_NUM_THREADS=16

# 缓存目录
HF_HOME=/workspace/cache
TRANSFORMERS_CACHE=/workspace/cache
TORCH_HOME=/workspace/cache
```

### 4. 卷挂载设置

```yaml
挂载配置:
- /workspace/outputs:/app/outputs  # 输出文件
- /workspace/cache:/app/cache      # 模型缓存
- /workspace/logs:/app/logs        # 日志文件
```

---

## 🚀 快速部署脚本

### 一键部署脚本
```bash
#!/bin/bash

echo "🔥 开始部署SkyReels V2无限制版..."

# 更新系统
apt-get update && apt-get upgrade -y

# 安装基础依赖
apt-get install -y git wget curl python3.10 python3-pip

# 克隆项目
git clone https://github.com/your-repo/skyreels-v2-unlimited.git /app
cd /app

# 构建Docker镜像
docker build -f Dockerfile.unlimited -t skyreels-v2:unlimited .

# 启动容器
docker run -d \
  --name skyreels-unlimited \
  --gpus all \
  -p 8000:8000 \
  -v /workspace/outputs:/app/outputs \
  -v /workspace/cache:/app/cache \
  -v /workspace/logs:/app/logs \
  -e SKYREELS_UNLIMITED_MODE=true \
  -e SKYREELS_MAX_DURATION=7200 \
  -e SKYREELS_ENABLE_4K=true \
  skyreels-v2:unlimited

echo "✅ 部署完成！"
echo "🌐 API地址: http://localhost:8000"
echo "📋 API文档: http://localhost:8000/docs"
```

---

## 🔧 手动部署步骤

### 1. 系统准备
```bash
# 连接到RunPod实例
ssh root@your-pod-ip

# 更新系统
apt-get update && apt-get upgrade -y

# 安装NVIDIA驱动和Docker (如果未安装)
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | tee /etc/apt/sources.list.d/nvidia-docker.list

apt-get update && apt-get install -y nvidia-docker2
systemctl restart docker
```

### 2. 下载项目代码
```bash
# 创建工作目录
mkdir -p /workspace/{outputs,cache,logs}
cd /workspace

# 克隆项目
git clone <your-skyreels-repo> skyreels-v2
cd skyreels-v2
```

### 3. 构建Docker镜像
```bash
# 构建无限制版镜像
docker build -f Dockerfile.unlimited -t skyreels-v2:unlimited .

# 查看镜像
docker images
```

### 4. 启动服务
```bash
# 启动无限制容器
docker run -d \
  --name skyreels-unlimited \
  --gpus all \
  --restart unless-stopped \
  -p 8000:8000 \
  -v /workspace/outputs:/app/outputs \
  -v /workspace/cache:/app/cache \
  -v /workspace/logs:/app/logs \
  -e SKYREELS_UNLIMITED_MODE=true \
  -e SKYREELS_MAX_RESOLUTION=1080p \
  -e SKYREELS_MAX_DURATION=7200 \
  -e SKYREELS_ENABLE_4K=true \
  -e SKYREELS_HIGH_QUALITY=true \
  -e PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:4096 \
  skyreels-v2:unlimited

# 查看启动状态
docker ps
docker logs skyreels-unlimited
```

---

## 📊 服务验证

### 1. 健康检查
```bash
# 检查服务状态
curl http://localhost:8000/health

# 查看GPU信息
curl http://localhost:8000/models/info

# 查看系统状态
curl http://localhost:8000/system/stats
```

### 2. 测试视频生成
```bash
# 测试短视频生成
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A beautiful sunset over the ocean with waves",
    "resolution": "720p",
    "duration": 30,
    "quality": "high"
  }'
```

### 3. 查看日志
```bash
# 查看API日志
docker logs -f skyreels-unlimited

# 查看GPU监控
tail -f /workspace/logs/gpu_monitor.log

# 查看系统监控
tail -f /workspace/logs/system_monitor.log
```

---

## 🔧 RunPod特定优化

### 1. 网络配置
```bash
# 设置RunPod代理 (自动配置)
export RUNPOD_POD_ID=$(curl -s http://metadata.runpod.io/v1/pod/id)
export PUBLIC_URL="https://${RUNPOD_POD_ID}-8000.proxy.runpod.net"

echo "🌐 Public URL: $PUBLIC_URL"
```

### 2. 持久化存储
```bash
# 创建持久化目录
mkdir -p /workspace/persistent/{models,outputs,cache}

# 软链接到应用目录
ln -sf /workspace/persistent/models /app/cache/models
ln -sf /workspace/persistent/outputs /app/outputs
ln -sf /workspace/persistent/cache /app/cache
```

### 3. 自动重启配置
```bash
# 创建systemd服务
cat > /etc/systemd/system/skyreels.service << 'EOF'
[Unit]
Description=SkyReels V2 Unlimited
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/bin/docker start skyreels-unlimited
ExecStop=/usr/bin/docker stop skyreels-unlimited

[Install]
WantedBy=multi-user.target
EOF

# 启用服务
systemctl enable skyreels.service
systemctl start skyreels.service
```

---

## 🎯 n8n工作流集成

### 1. 更新n8n工作流配置
```json
{
  "skyreelsEndpoint": "https://your-pod-id-8000.proxy.runpod.net"
}
```

### 2. 测试连接
```bash
# 在n8n中测试健康检查节点
GET https://your-pod-id-8000.proxy.runpod.net/health
```

---

## 📈 性能监控

### 1. GPU监控
```bash
# 实时GPU状态
watch -n 1 nvidia-smi

# GPU历史数据
tail -f /workspace/logs/gpu_monitor.log
```

### 2. API监控
```bash
# API访问日志
tail -f /workspace/logs/access.log

# API错误日志  
tail -f /workspace/logs/error.log
```

### 3. 系统监控
```bash
# 系统资源
htop

# 磁盘使用
df -h

# 内存使用
free -h
```

---

## 🛠️ 故障排除

### 常见问题解决

1. **GPU内存不足**
```bash
# 清理GPU缓存
curl -X POST http://localhost:8000/system/cleanup

# 重启容器
docker restart skyreels-unlimited
```

2. **服务无法启动**
```bash
# 查看详细日志
docker logs --details skyreels-unlimited

# 检查GPU可用性
nvidia-smi
```

3. **生成速度慢**
```bash
# 检查GPU使用率
nvidia-smi

# 优化环境变量
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:8192
export OMP_NUM_THREADS=32
```

---

## 💡 最佳实践

1. **定期清理**: 每天清理临时文件和旧任务
2. **监控资源**: 监控GPU内存和磁盘使用情况
3. **备份模型**: 定期备份下载的模型文件
4. **日志轮转**: 配置日志轮转避免磁盘满
5. **安全访问**: 使用RunPod内置的安全访问机制

---

部署完成后，您就拥有了一个支持无限制长视频生成的强大AI服务！🚀 
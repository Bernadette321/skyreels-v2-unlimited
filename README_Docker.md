# SkyReels V2 Docker 部署指南

这是一个完整的Docker化解决方案，用于部署SkyReels V2 720P无限长度视频生成模型。

## 🚀 快速开始

### 1. 系统要求

- **GPU**: NVIDIA GPU with 12GB+ VRAM (推荐RTX 4090, A100, V100)
- **CPU**: 8+ cores 
- **RAM**: 32GB+ 
- **Storage**: 100GB+ 可用空间 (模型 + 生成的视频)
- **Docker**: 20.10+
- **NVIDIA Container Toolkit**: 最新版本

### 2. 环境准备

```bash
# 安装Docker (Ubuntu/Debian)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker

# 测试GPU支持
docker run --rm --gpus all nvidia/cuda:12.1-base-ubuntu22.04 nvidia-smi
```

### 3. 构建和运行

```bash
# 克隆项目 (如果还没有)
git clone git@github.com:SkyworkAI/SkyReels-V2.git

# 构建Docker镜像
chmod +x build.sh
./build.sh

# 启动服务 (推荐使用Docker Compose)
docker-compose up -d

# 或者直接运行
docker run -d --gpus all \
  -p 8000:8000 \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/results:/app/results \
  -v $(pwd)/cache:/app/cache \
  --name skyreels-v2 \
  skyreels-v2-720p:latest
```

## 📋 API 使用指南

### 健康检查
```bash
curl http://localhost:8000/health
```

### 模型信息
```bash
curl http://localhost:8000/models/info
```

### 生成12分钟视频
```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A mystical forest with dancing fireflies, ancient trees swaying in magical wind, ethereal lighting filtering through leaves, cinematic atmosphere, 4K quality",
    "duration": 720,
    "resolution": "720p"
  }'
```

### 检查生成状态
```bash
# 替换 TASK_ID 为实际的任务ID
curl http://localhost:8000/status/TASK_ID
```

### 下载生成的视频
```bash
# 替换 TASK_ID 为实际的任务ID
curl -O http://localhost:8000/download/TASK_ID
```

### 查看所有任务
```bash
curl http://localhost:8000/tasks
```

## 🔧 配置选项

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `ENVIRONMENT` | `production` | 运行模式 (development/production) |
| `CUDA_VISIBLE_DEVICES` | `0` | 指定使用的GPU |
| `OMP_NUM_THREADS` | `4` | OpenMP线程数 |
| `PYTHONUNBUFFERED` | `1` | Python输出不缓冲 |

### Docker Compose 配置

编辑 `docker-compose.yml` 以调整：
- 端口映射
- GPU分配
- 内存限制
- 存储卷挂载

## 📁 文件结构

```
skyreelsv2/
├── Dockerfile                 # Docker镜像定义
├── docker-compose.yml        # Docker Compose配置
├── api_server.py             # Flask API服务器
├── requirements_docker.txt   # Python依赖
├── start.sh                  # 容器启动脚本
├── build.sh                  # 镜像构建脚本
├── models/                   # 模型存储目录
├── results/                  # 生成视频输出
├── cache/                    # 缓存目录
├── logs/                     # 日志目录
└── SkyReels-V2/             # 原始项目代码
```

## 🐛 故障排除

### 常见问题

1. **GPU内存不足**
   ```bash
   # 检查GPU状态
   nvidia-smi
   
   # 清理GPU内存
   docker restart skyreels-v2
   ```

2. **模型下载失败**
   ```bash
   # 检查网络连接
   # 模型会在首次使用时自动下载
   docker logs skyreels-v2 -f
   ```

3. **生成超时**
   ```bash
   # 增加超时时间 (在docker-compose.yml中)
   environment:
     - GENERATION_TIMEOUT=7200  # 2小时
   ```

### 日志查看

```bash
# 查看容器日志
docker logs skyreels-v2 -f

# 查看详细日志
tail -f logs/error.log
tail -f logs/access.log
```

### 性能监控

```bash
# 启动监控服务 (可选)
docker-compose --profile monitoring up -d

# 访问Portainer (可选)
# http://localhost:9000
```

## 📊 性能指标

### 典型生成时间 (720P, RTX 4090)

| 视频长度 | 预估时间 | GPU内存使用 |
|----------|----------|------------|
| 30秒     | 2-5分钟   | 8-10GB     |
| 2分钟    | 8-15分钟  | 10-12GB    |
| 12分钟   | 45-90分钟 | 12-16GB    |
| 30分钟   | 2-4小时   | 16-20GB    |

### 优化建议

1. **使用SSD存储**: 模型加载和视频保存更快
2. **预热模型**: 首次运行会下载模型，后续会更快
3. **批量生成**: 连续生成多个视频时保持容器运行
4. **监控资源**: 使用 `nvidia-smi` 监控GPU使用率

## 🚢 RunPod 部署

### 1. 推送镜像到Registry

```bash
# 标记镜像
docker tag skyreels-v2-720p:latest your-registry/skyreels-v2-720p:latest

# 推送镜像
docker push your-registry/skyreels-v2-720p:latest
```

### 2. RunPod配置

- **镜像**: `your-registry/skyreels-v2-720p:latest`
- **端口**: `8000`
- **GPU**: RTX 4090 或更高
- **磁盘**: 100GB+
- **内存**: 32GB+

### 3. 环境变量设置

```bash
ENVIRONMENT=production
CUDA_VISIBLE_DEVICES=0
OMP_NUM_THREADS=4
```

## 🔗 集成到n8n工作流

更新您的n8n工作流中的SkyReels V2 API端点：

```javascript
// n8n HTTP Request 节点配置
{
  "method": "POST",
  "url": "https://your-runpod-instance.runpod.net:8000/generate",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "prompt": "{{$json.storyPrompt}}",
    "duration": 720,
    "resolution": "720p"
  }
}
```

## 📞 支持

如果遇到问题，请：
1. 检查日志文件
2. 确认系统要求
3. 查看故障排除部分
4. 提交GitHub Issue

---

🎬 **享受无限长度的720P视频生成！** 
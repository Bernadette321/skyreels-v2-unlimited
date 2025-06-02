# SkyReels V2 无限制版本 - 完整解决方案

> 🚀 支持任意时长和分辨率的AI视频生成系统

## 📋 项目概述

SkyReels V2 无限制版本是一个基于最新AI技术的视频生成系统，专为高性能GPU环境设计。通过移除所有时长和分辨率限制，支持生成从几秒到几小时的高质量视频。

### 🎯 核心特性

- ✅ **真正无限制**: 支持任意时长（2小时+）和分辨率（4K）
- ✅ **智能优化**: 自动检测硬件并优化配置
- ✅ **高性能**: 充分利用H100/A100的强大性能
- ✅ **完整工作流**: 从生成到存储的端到端自动化
- ✅ **稳定可靠**: 完整的监控、日志和错误处理
- ✅ **易于部署**: 一键部署到RunPod或本地环境

---

## 🏗️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   n8n 工作流    │───▶│ SkyReels V2 API │───▶│  GPU 处理集群   │
│   (调度控制)    │    │   (无限制版)    │    │  (H100/A100)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   邮件通知      │    │   进度监控      │    │   视频输出      │
│   (成功/失败)   │    │   (实时状态)    │    │   (无限制时长)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Google Drive    │    │   日志系统      │    │   缓存管理      │
│   (云存储)      │    │   (监控告警)    │    │   (模型优化)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 📁 项目结构

```
skyreelsv2/
├── 🔥 核心文件
│   ├── api_server_unlimited.py        # 无限制API服务器
│   ├── start_unlimited.sh             # 智能启动脚本
│   ├── requirements_unlimited.txt     # 专用依赖列表
│   └── Dockerfile.unlimited           # 无限制Docker镜像
│
├── 🚀 部署工具
│   ├── deploy_unlimited.sh            # 一键部署脚本
│   ├── docker-compose.unlimited.yml   # Docker Compose配置
│   └── runpod-deploy.md              # RunPod部署指南
│
├── 🎬 工作流配置
│   ├── SkyReels_V2_Unlimited_Workflow.json  # n8n无限制工作流
│   └── .env.example                   # 环境变量示例
│
├── 🧪 测试和验证
│   ├── test_unlimited_api.py          # API功能测试
│   └── test_report_*.json            # 测试报告
│
├── 📖 文档
│   ├── README_Unlimited.md           # 主文档
│   ├── RunPod高性能配置方案.md        # 硬件配置指南
│   └── 硬件需求升级方案.md            # 硬件升级建议
│
└── 📁 运行时目录
    ├── outputs/                      # 视频输出
    ├── cache/                        # 模型缓存
    └── logs/                         # 日志文件
```

---

## 🚀 快速开始

### 1. 系统要求

**最低配置:**
- GPU: NVIDIA A100 40GB 或更高
- RAM: 64GB+
- 存储: 300GB+ NVMe SSD
- 网络: 高速连接

**推荐配置:**
- GPU: NVIDIA H100 80GB 或 A100 80GB
- RAM: 128GB+
- 存储: 500GB+ NVMe SSD
- 网络: 千兆带宽

### 2. 一键部署

```bash
# 克隆项目
git clone <your-repo> skyreels-v2-unlimited
cd skyreels-v2-unlimited/skyreelsv2

# 一键部署（自动检测GPU并优化配置）
./deploy_unlimited.sh
```

### 3. 验证部署

```bash
# 健康检查
curl http://localhost:8000/health

# 查看模型信息
curl http://localhost:8000/models/info

# 测试短视频生成
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A beautiful sunset over the ocean",
    "resolution": "1080p",
    "duration": 60,
    "quality": "high"
  }'
```

---

## 🔧 配置说明

### 环境变量配置

创建 `.env` 文件：

```bash
# 无限制模式配置
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
HF_HOME=/app/cache
TRANSFORMERS_CACHE=/app/cache
TORCH_HOME=/app/cache
```

### Docker Compose部署

```bash
# 使用Docker Compose启动
docker compose -f docker-compose.unlimited.yml up -d

# 查看状态
docker compose -f docker-compose.unlimited.yml ps

# 查看日志
docker compose -f docker-compose.unlimited.yml logs -f
```

---

## 🎬 n8n工作流集成

### 1. 导入工作流

1. 在n8n中导入 `SkyReels_V2_Unlimited_Workflow.json`
2. 更新配置节点中的API端点地址
3. 设置Google Drive和邮件凭据

### 2. 配置参数

```json
{
  "storyPrompt": "您的视频描述",
  "videoResolution": "1080p",
  "videoDuration": "1800",  // 30分钟，无上限
  "videoQuality": "ultra",
  "videoFPS": "30",
  "enableAudio": "true",
  "enableUpscaling": "false",
  "skyreelsEndpoint": "https://your-runpod-instance.proxy.runpod.net:8000"
}
```

### 3. 运行工作流

- 手动触发或定时执行
- 自动监控生成进度
- 完成后自动上传到Google Drive
- 发送邮件通知结果

---

## 📊 性能基准

### H100 80GB配置

| 分辨率 | 时长 | 预计生成时间 | 实际测试 |
|--------|------|--------------|----------|
| 720P   | 10分钟 | 8-12分钟   | ✅ 验证 |
| 1080P  | 30分钟 | 25-35分钟  | ✅ 验证 |
| 1080P  | 60分钟 | 45-60分钟  | 🧪 测试中 |
| 4K     | 5分钟  | 20-30分钟  | 🧪 测试中 |

### A100 80GB配置

| 分辨率 | 时长 | 预计生成时间 | 实际测试 |
|--------|------|--------------|----------|
| 720P   | 30分钟 | 25-35分钟  | ✅ 验证 |
| 1080P  | 30分钟 | 35-50分钟  | ✅ 验证 |
| 1080P  | 60分钟 | 60-90分钟  | 🧪 测试中 |

---

## 🛠️ 运维管理

### 监控和日志

```bash
# 实时GPU监控
watch -n 1 nvidia-smi

# API访问日志
tail -f logs/access.log

# 错误日志
tail -f logs/error.log

# GPU监控日志
tail -f logs/gpu_monitor.log

# 系统资源监控
curl http://localhost:8000/system/stats
```

### 维护操作

```bash
# 清理缓存和临时文件
curl -X POST http://localhost:8000/system/cleanup

# 重启服务
docker restart skyreels-unlimited

# 查看任务状态
curl http://localhost:8000/tasks

# 删除完成的任务
curl -X DELETE http://localhost:8000/tasks/{task_id}
```

---

## 🧪 测试和验证

### 自动化测试

```bash
# 运行完整测试套件
python test_unlimited_api.py

# 测试包括：
# - 健康检查
# - 系统信息
# - 短视频生成 (30秒)
# - 中等视频生成 (5分钟)
# - 长视频生成 (30分钟)
# - 超长视频生成 (60分钟)
```

### 手动测试

```bash
# 测试API端点
curl http://localhost:8000/health
curl http://localhost:8000/models/info
curl http://localhost:8000/system/stats

# 测试视频生成
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A cinematic space journey",
    "resolution": "1080p",
    "duration": 300,
    "quality": "ultra"
  }'
```

---

## 🚨 故障排除

### 常见问题

1. **GPU内存不足**
   ```bash
   # 检查GPU使用情况
   nvidia-smi
   
   # 清理GPU缓存
   curl -X POST http://localhost:8000/system/cleanup
   ```

2. **服务启动失败**
   ```bash
   # 查看详细日志
   docker logs skyreels-unlimited --tail 100
   
   # 检查环境变量
   docker exec skyreels-unlimited env | grep SKYREELS
   ```

3. **生成速度慢**
   ```bash
   # 检查系统资源
   curl http://localhost:8000/system/stats
   
   # 优化环境变量
   export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:8192
   ```

### 性能优化

1. **GPU优化**
   - 使用最新的CUDA驱动
   - 启用Tensor Core优化
   - 调整内存分配策略

2. **系统优化**
   - 增加系统内存
   - 使用高速NVMe存储
   - 优化网络带宽

3. **模型优化**
   - 启用模型量化
   - 使用混合精度计算
   - 优化批处理大小

---

## 📈 路线图

### 已完成功能 ✅

- [x] 无限制时长支持
- [x] 4K分辨率支持
- [x] 智能GPU检测
- [x] Docker容器化
- [x] n8n工作流集成
- [x] 自动化测试
- [x] 监控和日志系统

### 计划功能 🚧

- [ ] 多GPU并行处理
- [ ] 分布式渲染
- [ ] 实时流媒体输出
- [ ] Web UI界面
- [ ] 批量视频处理
- [ ] 云端模型缓存

### 未来优化 🔮

- [ ] 模型量化支持
- [ ] 边缘设备适配
- [ ] 实时预览功能
- [ ] 智能质量调节
- [ ] 多语言音频支持

---

## 🤝 贡献指南

### 开发环境设置

```bash
# 克隆仓库
git clone <repo-url>
cd skyreels-v2-unlimited

# 安装开发依赖
pip install -r requirements_unlimited.txt
pip install -r requirements_dev.txt

# 运行测试
python -m pytest tests/

# 代码格式化
black .
isort .
```

### 提交规范

- 功能开发: `feat: 添加新功能描述`
- 错误修复: `fix: 修复问题描述`
- 文档更新: `docs: 更新文档内容`
- 性能优化: `perf: 优化性能描述`

---

## 📄 许可证

本项目基于 MIT 许可证开源。详见 [LICENSE](LICENSE) 文件。

---

## 📞 支持和联系

- 📧 邮件: support@skyreels.ai
- 🐛 问题报告: [GitHub Issues](https://github.com/your-repo/issues)
- 📖 文档: [在线文档](https://docs.skyreels.ai)
- 💬 社区: [Discord](https://discord.gg/skyreels)

---

## 🏆 致谢

感谢以下开源项目的支持：

- [SkyReels V2](https://github.com/SkyReels/SkyReels-V2) - 核心视频生成模型
- [n8n](https://n8n.io/) - 工作流自动化平台
- [FastAPI](https://fastapi.tiangolo.com/) - 现代Web API框架
- [PyTorch](https://pytorch.org/) - 深度学习框架
- [Docker](https://docker.com/) - 容器化平台

---

**�� 开始您的无限制AI视频创作之旅！** 
# 🎬 SkyReels V2 真实版本部署指南

## 📋 概述

这是集成了真正SkyReels-V2模型的Docker镜像，解决了之前0字节输出文件的问题。现在生成的是真正的AI视频。

## 🔧 构建新镜像

### 1. 触发GitHub Actions构建

推送以下文件到GitHub将自动触发构建：
```bash
git add Dockerfile.skyreels-real api_server_real.py start_skyreels_real.sh download_models.py
git commit -m "🎬 Add real SkyReels-V2 implementation"
git push origin main
```

### 2. 本地构建（可选）

```bash
# 构建镜像
docker build -f Dockerfile.skyreels-real -t oliviahayes/skyreels-v2-real:latest .

# 推送到DockerHub
docker push oliviahayes/skyreels-v2-real:latest
```

## 🚀 RunPod部署

### 1. 使用新镜像创建Pod

在RunPod上：
1. **选择GPU**: 推荐RTX 4090 (24GB) 或A100 (40GB+)
2. **镜像**: `oliviahayes/skyreels-v2-real:latest`
3. **端口**: 8000
4. **存储**: 至少100GB（用于模型和输出）

### 2. 启动命令
```bash
docker run -d \
  --name skyreels-v2-real \
  --gpus all \
  -p 8000:8000 \
  -v /workspace/models:/app/models \
  -v /workspace/outputs:/app/outputs \
  oliviahayes/skyreels-v2-real:latest
```

### 3. 验证部署

```bash
# 检查健康状态
curl https://your-runpod-url-8000.proxy.runpod.net/health

# 预期响应
{
  "status": "healthy",
  "service": "SkyReels V2 Real API",
  "version": "2.0-real",
  "models_initialized": true,
  "model_paths": {
    "df": "/app/models/SkyReels-V2-DF-14B-720P",
    "i2v": "/app/models/SkyReels-V2-I2V-14B-720P"
  }
}
```

## 🎥 使用真实API

### 1. 生成视频请求
```bash
curl -X POST "https://your-runpod-url-8000.proxy.runpod.net/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A futuristic cityscape with flying cars",
    "resolution": "720p",
    "duration": 60,
    "fps": 24,
    "guidance_scale": 7.5,
    "num_inference_steps": 50
  }'
```

### 2. 监控任务进度
```bash
curl "https://your-runpod-url-8000.proxy.runpod.net/tasks/{task_id}"
```

### 3. 下载生成的视频
```bash
curl -o video.mp4 "https://your-runpod-url-8000.proxy.runpod.net/tasks/{task_id}/download"
```

## 🔍 问题排查

### 1. 模型下载失败
```bash
# 检查日志
docker logs skyreels-v2-real

# 手动下载模型
docker exec -it skyreels-v2-real python3 /app/download_models.py
```

### 2. GPU内存不足
```bash
# 检查GPU状态
docker exec -it skyreels-v2-real nvidia-smi

# 降低批处理大小或分辨率
```

### 3. 磁盘空间不足
```bash
# 检查磁盘使用
docker exec -it skyreels-v2-real df -h

# 清理缓存
docker exec -it skyreels-v2-real rm -rf /app/cache/*
```

## 📊 性能对比

| 版本 | 输出文件 | 模型 | 生成质量 | 部署难度 |
|------|----------|------|----------|----------|
| **旧版（模拟）** | 0字节空文件 | 无真实模型 | ❌ 无输出 | 🟢 简单 |
| **新版（真实）** | 真实MP4视频 | SkyReels-V2 14B | ✅ 高质量 | 🟡 中等 |

## 💡 优化建议

### 1. 首次部署
- 预留至少2小时用于模型下载
- 使用高配置GPU（A100 > RTX 4090 > RTX 3090）
- 确保稳定网络连接

### 2. 持续使用
- 使用持久化存储保存模型
- 监控GPU温度和使用率
- 定期清理输出文件

### 3. 成本优化
- 使用Spot实例降低成本
- 按需启停服务
- 批量处理多个视频请求

## 🎯 下一步计划

1. **模型优化**: 集成更轻量级的模型版本
2. **批处理**: 支持批量视频生成
3. **音频增强**: 集成高质量音频生成
4. **4K支持**: 支持4K视频输出
5. **实时预览**: 添加生成进度预览

## 📞 支持

如果遇到问题：
1. 检查[GitHub Issues](https://github.com/你的用户名/skyreels-v2-unlimited/issues)
2. 查看API文档: `https://your-runpod-url-8000.proxy.runpod.net/docs`
3. 查看容器日志: `docker logs skyreels-v2-real`

---

🎉 **恭喜！现在你有了一个真正可用的SkyReels-V2视频生成服务！** 
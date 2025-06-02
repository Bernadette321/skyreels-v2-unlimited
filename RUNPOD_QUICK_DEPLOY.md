# SkyReels-V2 RunPod 快速部署指南

## 🚀 一键部署命令

在RunPod Terminal中运行以下命令：

```bash
# 1. 进入workspace目录
cd /workspace

# 2. 下载部署脚本
curl -O https://raw.githubusercontent.com/Bernadette321/skyreels-v2-unlimited/main/runpod_deploy_real.sh

# 3. 给脚本执行权限
chmod +x runpod_deploy_real.sh

# 4. 运行一键部署
./runpod_deploy_real.sh
```

## 📋 手动部署步骤（如果一键部署失败）

### 1. 停止旧服务
```bash
pkill -f "api_server" || true
pkill -f "python.*api" || true
```

### 2. 下载新的实现
```bash
cd /workspace
git clone https://github.com/Bernadette321/skyreels-v2-unlimited.git skyreels-v2-real
cd skyreels-v2-real
```

### 3. 安装依赖
```bash
pip install --upgrade pip
pip install huggingface-hub
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install diffusers transformers accelerate
pip install fastapi uvicorn[standard] pydantic
pip install opencv-python-headless pillow numpy xformers
```

### 4. 下载模型（这是关键步骤！）
```bash
python3 download_models.py
```

### 5. 启动真实服务
```bash
mkdir -p logs
nohup python3 api_server_real.py > logs/api_server.log 2>&1 &
```

## 🔧 验证部署

### 检查服务状态
```bash
# 检查进程
ps aux | grep api_server_real

# 检查端口
netstat -tlnp | grep :8000

# 查看日志
tail -f logs/api_server.log
```

### 测试API
```bash
# 健康检查
curl http://localhost:8000/health

# 访问API文档
# 在浏览器中打开: http://你的RunPod端口:8000/docs
```

## ⚠️ 故障排除

### 模型下载失败
如果看到 "Repository Not Found" 错误：
```bash
# 确保使用正确的模型仓库名称
# 检查 download_models.py 中的仓库名称是否为 "Skywork/" 而不是 "SkyworkAI/"
grep "repo_id" download_models.py
```

### 磁盘空间不足
```bash
# 检查磁盘空间
df -h

# 清理空间
rm -rf ~/.cache/pip
rm -rf /tmp/*
```

### GPU不可用
```bash
# 检查GPU
nvidia-smi

# 检查CUDA
python3 -c "import torch; print(torch.cuda.is_available())"
```

## 📊 预期结果

成功部署后应该看到：
- ✅ 服务运行在 http://localhost:8000
- ✅ API文档可访问: http://localhost:8000/docs  
- ✅ 健康检查通过: http://localhost:8000/health
- ✅ 能够生成真实的视频文件（而不是0字节空文件）

## 🎬 测试视频生成

使用API文档界面或curl命令测试：

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A beautiful sunset over the ocean",
    "duration": 30,
    "resolution": "720p"
  }'
```

## 📞 获取帮助

如果遇到问题：
1. 检查日志文件: `tail -f logs/api_server.log`
2. 确认模型已正确下载到 `/workspace/skyreels-v2-real/models/`
3. 验证所有依赖已安装: `pip list | grep -E "(torch|diffusers|transformers)"`

---

**重要说明**: 这个部署使用真实的SkyReels-V2模型，会生成实际的视频文件，而不是之前的0字节空文件。首次模型下载可能需要30-60分钟，取决于网络速度。 
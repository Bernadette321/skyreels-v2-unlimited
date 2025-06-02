# SkyReels V2 Docker API n8n工作流使用指南

## 🎯 工作流概览

这个更新后的n8n工作流专门为我们的SkyReels V2 Docker API设计，提供完整的720P长视频生成和处理流程。

### ✨ 主要特性

- 🎬 **720P无限长度视频生成** (最大60分钟)
- 🔊 **原生音频支持** (相比Runway AI的无声视频)
- 🚀 **Diffusion Forcing技术** (最新AI视频生成技术)
- 📊 **实时进度监控** (异步处理状态跟踪)
- 🔧 **AI增强到1080P** (使用upscale.media)
- ☁️ **自动云端存储** (Google Drive)
- 📧 **智能邮件通知** (成功/失败通知)

## 🔧 部署步骤

### 1. 部署SkyReels V2 Docker容器

```bash
# 在RunPod或本地服务器
cd skyreelsv2
./build.sh
docker-compose up -d

# 测试API
python3 test_api.py
```

### 2. 更新n8n工作流配置

在"🎬 SkyReels V2 配置中心"节点中修改以下参数：

#### 基础配置
```javascript
{
  "storyName": "YourStoryName",
  "storyPrompt": "Your detailed story description in English",
  "videoStyle": "cinematic, fantasy, high quality, detailed animation, 720p",
  "skyreelsEndpoint": "https://your-runpod-instance.runpod.net:8000",
  "videoDuration": "720",  // 12分钟 = 720秒
  "videoResolution": "720p"
}
```

#### RunPod端点配置
- 获取您的RunPod实例URL
- 确保端口8000开放
- 格式：`https://your-instance-id.runpod.net:8000`

### 3. 配置Google Drive集成

1. **创建Google Drive文件夹**：
   - 创建专用文件夹存储视频
   - 获取文件夹ID（URL中的长字符串）
   - 更新工作流中的`parentIds`

2. **OAuth2认证**：
   - 在n8n中配置Google Drive凭据
   - 授权访问权限

### 4. 配置邮件通知

使用现有的Gmail SMTP配置：
```
Host: smtp.gmail.com
Port: 587
User: ovepetaicontact@gmail.com
Password: plnndfkfgkbstrcf
```

## 🚀 工作流执行流程

### 阶段1：初始化和检查
1. **配置加载** - 读取故事配置参数
2. **API健康检查** - 验证SkyReels V2服务状态
3. **生成请求** - 发送视频生成请求

### 阶段2：视频生成监控
1. **等待初始化** - 等待60秒让模型加载
2. **状态轮询** - 每2分钟检查生成进度
3. **完成检测** - 监控`completed`或`failed`状态

### 阶段3：文件处理和存储
1. **下载720P视频** - 从API下载生成的视频
2. **上传到Google Drive** - 存储720P原始版本
3. **AI增强处理** - 使用upscale.media增强到1080P
4. **上传1080P版本** - 存储增强后的视频

### 阶段4：通知和完成
1. **成功通知** - 发送包含下载链接的邮件
2. **失败处理** - 发送错误通知和建议解决方案

## 📋 API端点说明

### 健康检查
```bash
GET /health
# 返回：服务状态和推理引擎就绪状态
```

### 开始生成
```bash
POST /generate
Content-Type: application/json

{
  "prompt": "Detailed story description",
  "duration": 720,
  "resolution": "720p"
}

# 返回：task_id和预估完成时间
```

### 检查状态
```bash
GET /status/{task_id}
# 返回：状态、进度、错误信息等
```

### 下载视频
```bash
GET /download/{task_id}
# 返回：视频文件（当状态为completed时）
```

## 🎬 使用示例

### 示例1：神秘森林故事
```json
{
  "storyName": "MysticalForest",
  "storyPrompt": "A mystical forest with dancing fireflies, ancient trees swaying in magical wind, ethereal lighting filtering through leaves, cinematic atmosphere, 4K quality, fantasy adventure",
  "videoStyle": "cinematic, fantasy, high quality, detailed animation, 720p",
  "videoDuration": "720"
}
```

### 示例2：科幻太空故事
```json
{
  "storyName": "SpaceOdyssey",
  "storyPrompt": "A futuristic space station orbiting a distant planet, astronauts in sleek spacesuits exploring alien landscapes, advanced technology, stunning cosmic views, sci-fi cinematic style",
  "videoStyle": "sci-fi, cinematic, futuristic, high quality, space theme, 720p",
  "videoDuration": "1200"
}
```

## ⚡ 性能优化建议

### GPU配置
- **推荐GPU**: RTX 4090, A100, V100
- **最小VRAM**: 12GB
- **推荐VRAM**: 16GB+

### 时间预估
| 视频长度 | 预估生成时间 | GPU内存使用 |
|----------|-------------|------------|
| 30秒     | 2-5分钟     | 8-10GB     |
| 2分钟    | 8-15分钟    | 10-12GB    |
| 12分钟   | 45-90分钟   | 12-16GB    |
| 20分钟   | 1.5-3小时   | 16-20GB    |

### 优化提示
1. **预热模型** - 保持容器运行，避免重复初始化
2. **批量处理** - 连续生成多个视频更高效
3. **监控资源** - 使用`nvidia-smi`监控GPU状态
4. **网络优化** - 确保高带宽连接用于文件上传

## 🐛 常见问题和解决方案

### 1. API连接失败
```bash
# 检查容器状态
docker ps
docker logs skyreels-v2-api

# 测试API连通性
curl http://your-endpoint:8000/health
```

### 2. 生成超时
- 增加等待时间间隔
- 检查GPU内存是否充足
- 简化提示词

### 3. 上传失败
- 检查Google Drive API配额
- 验证OAuth2令牌有效性
- 确认文件夹权限

### 4. 邮件发送失败
- 验证SMTP配置
- 检查Gmail应用专用密码
- 确认收件人邮箱有效

## 🔍 监控和调试

### 查看日志
```bash
# 容器日志
docker logs skyreels-v2-api -f

# API访问日志
tail -f skyreelsv2/logs/access.log

# 错误日志
tail -f skyreelsv2/logs/error.log
```

### n8n调试
1. 启用详细日志记录
2. 检查每个节点的输出
3. 使用"测试步骤"功能逐步调试

## 🎉 最佳实践

### 提示词优化
- 使用英文描述
- 包含具体的视觉元素
- 指定风格和质量要求
- 控制在500字符以内

### 文件管理
- 使用有意义的故事名称
- 定期清理临时文件
- 监控存储空间使用

### 错误处理
- 设置合理的重试次数
- 添加超时保护
- 记录详细的错误信息

---

🎬 **现在您可以开始创作无限长度的720P高质量视频了！** 
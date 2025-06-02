# AI助手操作规范

## 🚨 **关键规则 - 必须遵守**

### 1. **严禁重复创建.github目录**
- ❌ **绝对禁止**: 在项目外层创建`.github`目录
- ✅ **正确做法**: 只使用已存在的`skyreelsv2/.github/`目录
- ⚠️ **验证步骤**: 每次文件操作后立即执行 `find . -name ".github" -type d`

### 2. **文件操作前必须确认路径**
```bash
# 标准操作流程
1. pwd                              # 确认当前目录
2. ls -la .github/workflows/        # 确认目标目录存在
3. edit_file("正确的相对路径")       # 执行操作
4. find . -name ".github" -type d   # 验证结果
```

### 3. **目录结构认知**
```
正确的项目结构:
/Users/bernadette/Desktop/project_n8n/
├── skyreelsv2/                    ← GitHub仓库根目录
│   ├── .github/workflows/         ← 唯一正确的.github位置
│   ├── Dockerfile.unlimited
│   └── [其他项目文件]
└── [其他无关文件]
```

## 📋 **文件操作检查清单**

### 在执行任何.github相关操作前：
- [ ] 确认当前在 `/project_n8n/skyreelsv2` 目录
- [ ] 确认 `.github/workflows/` 目录已存在
- [ ] 使用相对路径：`.github/workflows/filename.yml`
- [ ] 操作后立即验证：`find . -name ".github" -type d` 应该只返回一个结果

### 如果发现错误：
- [ ] 立即执行：`rm -rf /Users/bernadette/Desktop/project_n8n/.github`
- [ ] 确认只剩一个：`find /Users/bernadette/Desktop/project_n8n -name ".github" -type d`
- [ ] 重新在正确位置操作

## 🔧 **工具使用最佳实践**

### edit_file 工具
```python
# ✅ 推荐做法
1. 先确认当前目录：run_terminal_cmd("pwd")
2. 使用相对路径：edit_file(".github/workflows/docker-build.yml")
3. 立即验证：run_terminal_cmd("ls -la .github/workflows/")

# ❌ 避免做法  
- 不要假设工作目录
- 不要在不确定路径的情况下创建.github
```

### run_terminal_cmd 工具
```bash
# ✅ 每次重要操作前
pwd                                 # 确认位置
ls -la                             # 查看当前目录内容
git remote -v                      # 确认Git仓库

# ✅ 每次文件操作后
find . -name ".github" -type d     # 验证.github目录数量
```

## 🎯 **错误模式识别**

### 我曾经犯过的错误：
1. **重复创建.github** - 已发生 5+ 次
2. **路径假设错误** - 假设edit_file在当前shell目录工作
3. **缺乏验证步骤** - 操作后不立即检查结果
4. **固化思维** - 重复使用失败的解决模式

### 触发警报的情况：
- 当看到 `find . -name ".github" -type d` 返回多个结果
- 当用户说"你又创建了.github"
- 当文件操作后路径不符合预期

## 📞 **使用说明**

### 对于用户：
在新对话开始时，请提供这个文档并说：
"请严格遵守这个操作规范，特别是.github目录的创建规则"

### 对于AI助手：
1. **首先阅读**这个规范
2. **严格遵守**所有规则
3. **每次操作前**参考检查清单
4. **出现错误时**立即按规范纠正

## 🚀 **项目特定信息**

### SkyReels V2 项目：
- **仓库**: git@github.com:Bernadette321/skyreels-v2-unlimited.git
- **正确工作目录**: `/Users/bernadette/Desktop/project_n8n/skyreelsv2`
- **Docker用户名**: `oliviahayes`
- **镜像名称**: `oliviahayes/skyreels-v2-unlimited:latest`

### GitHub Actions：
- **工作流文件**: `.github/workflows/docker-build.yml`
- **Secrets配置**: DOCKERHUB_USERNAME, DOCKERHUB_TOKEN
- **构建结果**: https://hub.docker.com/repository/docker/oliviahayes/skyreels-v2-unlimited

---

**最后提醒**: 这些规则是血泪教训的总结，请严格遵守！ 
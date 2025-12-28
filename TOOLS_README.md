# 诊断和修复工具说明

本项目提供了一套完整的诊断和修复工具，帮助您快速解决常见问题。

## 🔍 诊断工具

### 1. diagnose.py - 综合环境诊断（必备）⭐

**用途**：自动检测所有依赖、模型、GPU配置问题，并提供针对性修复建议。

**使用方法**：
```bash
python diagnose.py
```

**检查项目**：
- ✅ 系统信息和Python架构（检测Rosetta 2）
- ✅ 所有Python依赖版本
- ✅ Florence-2模型是否可导入
- ✅ LaMA模型文件是否存在
- ✅ GPU/MPS加速是否可用
- ✅ 性能测试（Mac M1）

**输出示例**：
```
✅ Python架构: ARM64 (原生)
✅ transformers: 4.57.3 (>= 4.38.1)
✅ Florence2ForConditionalGeneration 可以导入
✅ LaMA模型文件存在: ~/.cache/torch/hub/checkpoints/big-lama.pt
✅ MPS (Apple GPU) 可用

所有检查通过！环境配置正确。
```

**何时使用**：
- 首次安装后验证环境
- 遇到任何错误时
- 升级依赖后验证
- 报告问题前收集环境信息

---

### 2. debug_detection.py - 水印检测测试

**用途**：测试单张图片/视频帧的水印检测是否正常工作。

**使用方法**：
```bash
# 基础用法
python debug_detection.py video.mp4

# 自定义检测提示词
python debug_detection.py video.mp4 "Sora watermark"

# 自定义最大面积百分比
python debug_detection.py video.mp4 "watermark" 15.0
```

**功能**：
- 提取视频中间帧或加载图片
- 使用Florence-2检测水印
- 生成标注图片显示检测结果
- 输出检测到的水印数量、位置、大小

**输出**：
- 控制台输出：检测详情
- 文件输出：`*_detected.png`（带标注的图片）

**何时使用**：
- 水印没有被移除时
- 验证检测参数是否正确
- 测试不同的 `detection_prompt`
- 测试不同的 `max_bbox_percent`

---

### 3. check_performance.py - 性能检查（Mac M1专用）

**用途**：检查Mac M1/M2/M3的Python架构和MPS性能。

**使用方法**：
```bash
python check_performance.py
```

**检查项目**：
- Python架构（ARM64 vs x86_64）
- MPS GPU性能测试
- 与CPU性能对比

**输出示例**：
```
✅ Python架构: ARM64 (原生)
MPS性能测试: 3.5x 加速

或：

❌ Python架构: Intel x86_64 (Rosetta 2转译)
MPS性能测试: 0.67x (比CPU慢!)
⚠️  建议安装ARM64原生Python以获得完整GPU加速
```

**何时使用**：
- Mac用户处理速度慢时
- 验证是否运行在Rosetta 2下
- 评估MPS加速效果

---

## 🔧 修复工具

### 4. fix_dependencies.sh - 自动修复依赖

**用途**：一键修复所有依赖问题。

**使用方法**：
```bash
bash fix_dependencies.sh
```

**功能**：
1. 检查当前transformers版本
2. 升级transformers到4.57.3（如果需要）
3. 升级timm和einops
4. 安装requirements.txt中的依赖
5. 安装iopaint（使用--no-deps）
6. 下载LaMA模型
7. 验证所有组件

**何时使用**：
- `diagnose.py` 报告依赖问题时
- 手动安装失败时
- 需要重新安装所有依赖时

---

### 5. install.py - 标准安装脚本

**用途**：首次安装或重新安装。

**使用方法**：
```bash
python install.py
```

**功能**：
- 检测现有依赖版本
- 只安装缺失的依赖
- 下载LaMA模型

**何时使用**：
- 首次安装
- 添加到新的ComfyUI环境

---

## 📖 文档资源

### 6. QUICK_START.md - 快速开始指南

**内容**：
- 常见问题速查表
- 快速修复命令
- 完整安装流程
- 工作流示例
- 性能优化建议

**适合人群**：新用户、遇到问题需要快速解决的用户

---

### 7. TROUBLESHOOTING.md - 详细故障排查

**内容**：
- 水印移除问题详细分析
- 检测参数调优指南
- 性能优化深度解析
- 代码对比分析

**适合人群**：遇到复杂问题、需要深入理解的用户

---

### 8. CLAUDE.md - 开发文档

**内容**：
- 项目架构说明
- 核心算法解析
- 常用命令
- 开发指南
- 技术细节

**适合人群**：开发者、需要修改代码的用户

---

## 🚀 使用流程推荐

### 新用户首次安装

```bash
# 1. 克隆仓库
cd /path/to/ComfyUI/custom_nodes
git clone <this-repo>

# 2. 运行安装
cd ComfyUI-JM-Sora-Watermark-Remover
python install.py

# 3. 验证环境
python diagnose.py

# 4. 重启ComfyUI
```

### 遇到问题时

```bash
# 1. 运行诊断（最重要！）
python diagnose.py

# 2. 根据诊断结果运行修复
bash fix_dependencies.sh

# 3. 如果是水印检测问题
python debug_detection.py your_video.mp4

# 4. 如果是Mac性能问题
python check_performance.py

# 5. 再次验证
python diagnose.py
```

### 报告问题时

请提供以下信息：

```bash
# 1. 诊断输出
python diagnose.py > diagnosis.txt

# 2. 系统信息
python -c "import sys, platform; print(f'Python: {sys.version}\nOS: {platform.platform()}')"

# 3. 如果是检测问题，附上
python debug_detection.py video.mp4
# 生成的 *_detected.png 文件
```

---

## 📊 工具对比表

| 工具 | 用途 | 运行时间 | 输出 | 必备程度 |
|------|------|---------|------|----------|
| **diagnose.py** | 全面诊断 | ~5秒 | 文本报告 | ⭐⭐⭐⭐⭐ |
| **fix_dependencies.sh** | 自动修复 | ~2分钟 | 安装日志 | ⭐⭐⭐⭐ |
| **debug_detection.py** | 检测测试 | ~10秒 | 标注图片 | ⭐⭐⭐⭐ |
| **check_performance.py** | 性能测试 | ~3秒 | 性能报告 | ⭐⭐⭐ (Mac) |
| **install.py** | 标准安装 | ~2分钟 | 安装日志 | ⭐⭐⭐⭐ |

---

## 💡 最佳实践

### ✅ 推荐做法

1. **首次安装后必须运行**：`python diagnose.py`
2. **遇到错误立即运行**：`python diagnose.py`
3. **升级依赖后验证**：`python diagnose.py`
4. **报告问题时附上**：`diagnose.py` 的完整输出

### ❌ 避免做法

1. ❌ 不运行诊断就手动修复
2. ❌ 忽略诊断脚本的警告
3. ❌ 不看文档就修改代码
4. ❌ 报告问题时不提供诊断信息

---

## 🆘 获取帮助

如果工具无法解决问题：

1. **查看文档**：
   - [QUICK_START.md](QUICK_START.md)
   - [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

2. **提交Issue**：
   - 包含 `diagnose.py` 完整输出
   - 说明您尝试过的解决方案
   - 附上相关截图或日志

3. **社区讨论**：
   - GitHub Discussions
   - 相关论坛

---

**记住**：90%的问题都可以通过运行 `python diagnose.py` 和阅读输出来解决！

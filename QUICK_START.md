# 快速开始指南

## 遇到问题？先运行诊断！

如果遇到任何问题，**首先运行诊断脚本**：

```bash
cd /path/to/ComfyUI-JM-Sora-Watermark-Remover
python diagnose.py
```

诊断脚本会自动检测所有问题并提供修复建议。

---

## 常见问题速查

### ❌ 错误：`cannot import name 'Florence2ForConditionalGeneration'`

**原因**：transformers版本过低或恰好是4.38.0

**快速修复**：

```bash
# Mac用户
pip install --upgrade transformers==4.57.3

# Linux用户（如果使用conda）
conda activate your_env
pip install --upgrade transformers==4.57.3

# 或使用修复脚本
bash fix_dependencies.sh
```

**详细说明**：transformers 4.38.0不包含Florence2，必须是4.38.1或更高版本。

---

### 🐌 处理速度很慢

#### Mac M1/M2/M3 用户

**检查Python架构**：

```bash
file $(which python)
```

如果显示 `x86_64`（Intel），说明运行在Rosetta 2下，性能损失30-50%。

**解决方案A**：安装ARM64原生Python（推荐）

```bash
# 下载ARM64版Miniforge
curl -L -O https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-arm64.sh

# 安装
bash Miniforge3-MacOSX-arm64.sh

# 重新创建环境并安装ComfyUI
```

**解决方案B**：优化当前环境参数

在ComfyUI中修改节点参数：
```
detection_skip: 5        # 每5帧检测一次（而不是1）
fade_in: 1.0
fade_out: 1.0
```

#### Linux/Windows 用户

**检查GPU加速**：

```bash
python -c "import torch; print(f'CUDA可用: {torch.cuda.is_available()}')"
```

如果显示 `False`，需要安装CUDA版本的PyTorch。

**优化参数**：
```
detection_skip: 3-5      # 减少检测帧数
```

---

### 💾 LaMA模型未找到

**错误信息**：`LaMA model not found` 或 `Failed to load LaMA model`

**快速修复**：

```bash
# 方法1: 运行安装脚本
python install.py

# 方法2: 手动下载
mkdir -p ~/.cache/torch/hub/checkpoints
curl -L -o ~/.cache/torch/hub/checkpoints/big-lama.pt \
  https://github.com/Sanster/models/releases/download/add_big_lama/big-lama.pt

# 验证文件大小
ls -lh ~/.cache/torch/hub/checkpoints/big-lama.pt
# 应该约196MB
```

---

### 🎯 水印没有被移除

#### 步骤1：运行检测诊断

```bash
python debug_detection.py your_video.mp4
```

这会生成一个 `*_detected.png` 文件，显示检测到的水印位置。

#### 步骤2：根据结果调整参数

**如果检测到了水印**（标注图片中有绿色框）：
- 问题可能在LaMA修复
- 确认 `transparent: false`（使用AI修复而非白色填充）
- 检查LaMA模型是否正常下载

**如果没检测到水印**（标注图片中没有框）：
- 调整 `detection_prompt`：
  - 尝试 `"Sora watermark"`
  - 尝试 `"Sora logo"`
  - 尝试 `"logo"`
- 增大 `max_bbox_percent`：
  - 从 `10.0` 增加到 `15.0` 或 `20.0`

#### 步骤3：优化视频处理参数

```
detection_skip: 3        # 每3帧检测一次
fade_in: 1.0            # 处理淡入效果
fade_out: 1.0           # 处理淡出效果
detection_prompt: "Sora watermark"
max_bbox_percent: 15.0
transparent: false
```

---

## 完整安装流程

### Mac (Intel 或 M1/M2/M3)

```bash
# 1. 克隆到ComfyUI的custom_nodes目录
cd /path/to/ComfyUI/custom_nodes
git clone https://github.com/yourusername/ComfyUI-JM-Sora-Watermark-Remover.git

# 2. 进入目录
cd ComfyUI-JM-Sora-Watermark-Remover

# 3. 运行安装脚本
python install.py

# 4. 如果遇到问题，运行修复脚本
bash fix_dependencies.sh

# 5. 运行诊断验证
python diagnose.py

# 6. 重启ComfyUI
```

### Linux (Ubuntu/Debian)

```bash
# 1. 激活ComfyUI的conda环境（如果使用conda）
conda activate comfyui

# 2. 克隆到ComfyUI的custom_nodes目录
cd /path/to/ComfyUI/custom_nodes
git clone https://github.com/yourusername/ComfyUI-JM-Sora-Watermark-Remover.git

# 3. 进入目录
cd ComfyUI-JM-Sora-Watermark-Remover

# 4. 运行安装脚本
python install.py

# 5. 如果遇到问题，运行修复脚本
bash fix_dependencies.sh

# 6. 运行诊断验证
python diagnose.py

# 7. 重启ComfyUI
```

### Windows

```powershell
# 1. 克隆到ComfyUI的custom_nodes目录
cd C:\path\to\ComfyUI\custom_nodes
git clone https://github.com/yourusername/ComfyUI-JM-Sora-Watermark-Remover.git

# 2. 进入目录
cd ComfyUI-JM-Sora-Watermark-Remover

# 3. 运行安装脚本
python install.py

# 4. 运行诊断验证
python diagnose.py

# 5. 重启ComfyUI
```

---

## 工作流示例

### 基础图像处理

```
Load Image → Sora Watermark Remover (Image) → Save Image
```

参数设置：
```
detection_prompt: "watermark"
max_bbox_percent: 10.0
transparent: false
```

### 视频处理（推荐设置）

```
Load Video → Sora Watermark Remover (Video) → Video Combine
```

参数设置：
```
detection_prompt: "Sora watermark"
max_bbox_percent: 10.0
fps: 30.0
detection_skip: 3
fade_in: 0.5
fade_out: 0.5
transparent: false
```

---

## 故障排查工具

本项目提供了完整的诊断工具集：

| 工具 | 用途 | 命令 |
|------|------|------|
| **diagnose.py** | 综合环境诊断 | `python diagnose.py` |
| **debug_detection.py** | 测试水印检测 | `python debug_detection.py video.mp4` |
| **fix_dependencies.sh** | 自动修复依赖 | `bash fix_dependencies.sh` |
| **check_performance.py** | 检查性能（Mac M1） | `python check_performance.py` |

---

## 获取帮助

1. **查看详细文档**：
   - [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - 详细的故障排查指南
   - [CLAUDE.md](CLAUDE.md) - 项目架构和开发指南
   - [README.md](README.md) - 完整功能说明

2. **运行诊断**：
   ```bash
   python diagnose.py
   ```

3. **提交Issue**：
   - 附上 `diagnose.py` 的完整输出
   - 附上错误日志
   - 说明您的系统环境（Mac/Linux/Windows）

---

## 性能优化建议

### Mac M1/M2/M3

- ✅ **推荐**：使用ARM64原生Python（性能提升30-50%）
- ✅ **设置**：`detection_skip: 3-5`
- ⚠️ **避免**：使用Intel版本Python（Rosetta 2）

### Linux with GPU

- ✅ **推荐**：安装CUDA版本PyTorch
- ✅ **设置**：`detection_skip: 3`
- ✅ **优化**：使用较小的视频分辨率（720p）

### 通用优化

| 参数 | 速度 | 质量 | 适用场景 |
|------|------|------|---------|
| `detection_skip: 1` | 慢 | 最高 | 最终输出 |
| `detection_skip: 3` | 中 | 高 | **推荐** ✅ |
| `detection_skip: 5` | 快 | 中 | 长视频/预览 |
| `transparent: true` | 极快 | 低 | 测试检测 |

---

## 版本要求

| 依赖 | 最低版本 | 推荐版本 | 注意事项 |
|------|---------|---------|---------|
| Python | 3.10 | 3.10/3.11 | - |
| transformers | 4.38.1 | 4.57.3 | ⚠️ 不是4.38.0 |
| timm | 0.9.0 | 1.0.22 | - |
| einops | 0.7.0 | 0.8.1 | - |
| torch | 2.0.0 | 2.2.2+ | MPS需要2.0+ |
| iopaint | - | 1.6.0 | 用--no-deps安装 |

---

**记住**：遇到任何问题，先运行 `python diagnose.py` ！

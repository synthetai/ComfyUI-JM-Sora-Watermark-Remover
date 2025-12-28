# ComfyUI-JM-Sora-Watermark-Remover

一个用于移除Sora和Sora2视频生成模型水印的ComfyUI自定义节点。

## 📚 文档导航

> 📖 **[完整文档索引](INDEX.md)** - 查看所有文档和工具

### 核心文档
- 🚀 **[快速开始指南](QUICK_START.md)** ⭐ 新手必读，常见问题快速解决
- 🔧 **[故障排查指南](TROUBLESHOOTING.md)** - 详细的问题诊断和解决方案
- 🛠️ **[诊断工具说明](TOOLS_README.md)** - 所有诊断工具的详细用法
- 💻 **[开发文档](CLAUDE.md)** - 项目架构和开发指南

## 🛠️ 诊断工具

遇到问题？运行诊断脚本自动检测：
```bash
python diagnose.py
```

所有可用工具：[TOOLS_README.md](TOOLS_README.md) | [DIAGNOSTIC_TOOLS.md](DIAGNOSTIC_TOOLS.md)

## 功能特性

- **AI智能检测** - 使用Florence-2模型进行水印智能检测
- **无痕移除** - 使用LaMA修复模型自然填充水印区域
- **视频处理** - 支持Sora/Sora2视频水印移除（两遍处理算法）
- **自定义检测** - 支持自定义检测提示词，适配不同水印类型
- **稀疏检测** - 视频处理时支持跳帧检测，提升处理效率
- **渐变处理** - 支持fade-in/fade-out水印的时间扩展
- **GPU加速** - 支持CUDA加速处理
- **批量处理** - ComfyUI原生支持批量图像处理

## 安装方法

### 方法1: 自动安装（推荐）

1. 将此仓库克隆到ComfyUI的custom_nodes目录：

```bash
cd /path/to/ComfyUI/custom_nodes
git clone https://github.com/yourusername/ComfyUI-JM-Sora-Watermark-Remover.git
```

2. 运行安装脚本：

```bash
cd ComfyUI-JM-Sora-Watermark-Remover
python install.py
```

3. 重启ComfyUI

### 方法2: 手动安装

1. 将此仓库克隆到ComfyUI的custom_nodes目录

2. 安装Python依赖：

```bash
cd ComfyUI-JM-Sora-Watermark-Remover

# 安装基础依赖
pip install -r requirements.txt

# 安装iopaint（用--no-deps避免依赖冲突）
pip install iopaint --no-deps
```

3. 手动下载LaMA模型：

```bash
mkdir -p ~/.cache/torch/hub/checkpoints
curl -L -o ~/.cache/torch/hub/checkpoints/big-lama.pt \
  https://github.com/Sanster/models/releases/download/add_big_lama/big-lama.pt
```

## 模型说明

本节点使用以下AI模型：

### 1. Florence-2-large (水印检测)
- **来源**: Microsoft Florence-2
- **HuggingFace**: `florence-community/Florence-2-large`
- **大小**: 约1GB
- **下载方式**: 首次使用时自动从HuggingFace下载
- **存储位置**: `~/.cache/huggingface/hub/`

### 2. LaMA (图像修复)
- **来源**: LaMA (Large Mask Inpainting)
- **大小**: 约196MB
- **存储位置**: `~/.cache/torch/hub/checkpoints/big-lama.pt`
- **下载方式**:
  - 自动安装：运行 `python install.py`
  - 手动安装：
    ```bash
    mkdir -p ~/.cache/torch/hub/checkpoints
    curl -L -o ~/.cache/torch/hub/checkpoints/big-lama.pt \
      https://github.com/Sanster/models/releases/download/add_big_lama/big-lama.pt
    ```

## 使用说明

### 节点类型

本插件提供两个节点：

#### 1. Sora Watermark Remover (Image)
用于处理单张图像或图像批次

#### 2. Sora Watermark Remover (Video)
用于处理视频帧序列，支持稀疏检测和时间扩展

### 节点参数说明

#### 图像节点参数（Image）

##### 必需参数
- **image**: 输入图像（ComfyUI的IMAGE类型）
- **detection_prompt**: 检测提示词
  - 默认值: `"watermark"`
  - 示例:
    - `"watermark"` - 检测通用水印
    - `"Sora watermark"` - 检测Sora水印
    - `"Sora logo"` - 检测Sora logo
    - `"Getty Images"` - 检测Getty Images水印
- **max_bbox_percent**: 最大检测框百分比
  - 默认值: `10.0`
  - 范围: `0.0 - 100.0`
  - 说明: 超过此百分比的检测框将被忽略，防止误检测大面积区域

##### 可选参数
- **transparent**: 透明模式
  - 默认值: `False`
  - 说明:
    - `False`: 使用LaMA模型修复水印区域
    - `True`: 将水印区域设为透明（用白色填充）

#### 视频节点参数（Video）

##### 必需参数
- **frames**: 视频帧序列（ComfyUI的IMAGE批次，批次维度表示帧数）
- **detection_prompt**: 检测提示词（同图像节点）
- **max_bbox_percent**: 最大检测框百分比（同图像节点）
- **fps**: 视频帧率
  - 默认值: `30.0`
  - 范围: `1.0 - 120.0`
  - 说明: 用于计算fade-in/fade-out的帧数

##### 可选参数
- **detection_skip**: 检测跳帧数
  - 默认值: `1`
  - 范围: `1 - 10`
  - 说明: 每N帧检测一次水印，提高处理效率。值越大越快，但可能错过短暂出现的水印
  - 推荐: Sora视频使用 `3-5`，水印位置固定的视频可用更大值

- **fade_in**: 渐入扩展时间（秒）
  - 默认值: `0.0`
  - 范围: `0.0 - 10.0`
  - 说明: 向前扩展mask的秒数，用于处理渐入水印
  - 推荐: 如果水印有渐入效果，设置为 `0.5 - 1.0`

- **fade_out**: 渐出扩展时间（秒）
  - 默认值: `0.0`
  - 范围: `0.0 - 10.0`
  - 说明: 向后扩展mask的秒数，用于处理渐出水印
  - 推荐: 如果水印有渐出效果，设置为 `0.5 - 1.0`

- **transparent**: 透明模式（同图像节点）

### 工作流示例

#### 图像处理工作流
```
Load Image → Sora Watermark Remover (Image) → Save Image
```

#### 视频处理工作流
```
Load Video (VHS) → Sora Watermark Remover (Video) → Save Video (VHS)
```

或使用ComfyUI的其他视频加载节点：
```
Video Loader → Sora Watermark Remover (Video) → Video Combiner
```

### 节点位置

在ComfyUI节点菜单中的位置：
```
JM-Nodes → Video → Sora → Sora Watermark Remover (Image)
JM-Nodes → Video → Sora → Sora Watermark Remover (Video)
```

## 参数调优建议

### detection_prompt（检测提示词）

根据不同的水印类型使用不同的提示词：

- **Sora水印**: `"Sora watermark"`, `"Sora logo"`, `"watermark"`
- **其他AI视频平台**: `"Runway watermark"`, `"Pika watermark"`
- **图库水印**: `"Getty Images"`, `"Shutterstock"`
- **通用检测**: `"watermark"`, `"logo"`

### max_bbox_percent（最大检测框百分比）

- **默认值 10%**: 适用于大多数常规水印
- **增大到 15-20%**: 如果水印较大但被漏检
- **减小到 5-8%**: 如果误检测了非水印区域

### 视频处理参数优化

#### detection_skip（检测跳帧）
- **1**: 每帧都检测（最准确，最慢）
- **3-5**: Sora视频推荐值（平衡速度和质量）
- **7-10**: 水印位置完全固定时使用（最快）

#### fade_in/fade_out（渐变处理）
- **0.0**: 无渐变效果的水印
- **0.5**: 轻微渐变的水印
- **1.0-2.0**: 明显渐变的水印

### 处理模式选择

#### transparent（透明模式）
- **False (推荐)**: 使用AI修复，效果最自然，适合大多数场景
- **True**: 快速处理，适用于需要透明背景或快速预览的场景

## 视频处理原理

### 两遍处理算法

视频节点使用高效的两遍处理算法：

#### Pass 1: 稀疏检测
- 每 N 帧检测一次水印（由 `detection_skip` 控制）
- 记录检测到的水印位置（bbox）
- 大幅减少检测计算量

#### Pass 2: 时间扩展 + 修复
- 根据 `fade_in`/`fade_out` 参数扩展检测时间线
- 对所有需要处理的帧应用LaMA修复
- 未检测到水印的帧直接保留原始内容

### 处理流程示例

假设视频有100帧，参数设置为：
- `detection_skip = 5`
- `fade_in = 0.5秒` (30fps下为15帧)
- `fade_out = 0.5秒` (30fps下为15帧)

处理过程：
1. 在第 0, 5, 10, 15... 95 帧进行检测（共20次检测）
2. 如果第10帧检测到水印，则第0-25帧都会应用该水印mask
3. 最终只有包含水印的帧会被修复，其他帧保持原样

## 技术栈

- **Florence-2** - Microsoft视觉模型，用于水印检测
- **LaMA** - Large Mask Inpainting模型，用于图像修复
- **PyTorch** - 深度学习框架
- **Transformers** - HuggingFace模型库
- **IOPaint** - 图像修复工具包（提供LaMA模型加载和推理接口）
  - 注意：使用 `--no-deps` 方式安装以避免依赖冲突

## 系统要求

- Python 3.10+
- ComfyUI
- CUDA支持（可选，但强烈推荐用于GPU加速）
- 至少8GB内存（推荐16GB用于视频处理）
- 至少5GB磁盘空间（用于模型存储）

## 兼容性说明

本插件设计为**与ComfyUI环境完全兼容**：

✅ **自动适配ComfyUI已有依赖** - 使用ComfyUI已安装的包版本，不强制升级
✅ **延迟导入** - 模型相关依赖只在使用时加载，避免启动冲突
✅ **跨平台兼容** - 在macOS、Linux、Windows上均可运行
✅ **无需升级peft/diffusers** - 兼容旧版本依赖

### 依赖策略

1. **基础依赖**：transformers、opencv、pillow等
2. **iopaint**：使用`--no-deps`安装，避免依赖冲突
3. **可选依赖**：peft、diffusers使用ComfyUI已有版本
4. **延迟导入**：启动时不加载模型依赖，运行时才加载

## 常见问题

> 💡 **遇到问题？**
> 1. 运行诊断脚本：`python diagnose.py`
> 2. 查看 **[快速开始指南](QUICK_START.md)**
> 3. 查看 **[详细故障排查](TROUBLESHOOTING.md)**

### Q: ComfyUI启动时报错导入失败？
A: 请运行安装脚本：

```bash
cd ComfyUI-JM-Sora-Watermark-Remover
python install.py
```

如果还有问题，运行诊断：
```bash
python diagnose.py
```

install.py会：
- 检查现有依赖版本
- 只安装缺失的必需依赖
- 使用ComfyUI已有的包（避免冲突）
- 下载LaMA模型

### Q: 首次使用时很慢？
A: Florence-2模型会在首次使用时从HuggingFace下载（约1GB），请耐心等待。LaMA模型需要提前通过install.py安装。

### Q: 如何手动下载模型？
A:
```bash
# 下载LaMA模型（约196MB）
mkdir -p ~/.cache/torch/hub/checkpoints
curl -L -o ~/.cache/torch/hub/checkpoints/big-lama.pt \
  https://github.com/Sanster/models/releases/download/add_big_lama/big-lama.pt

# Florence-2模型会在首次使用时自动下载到
# ~/.cache/huggingface/hub/
```

### Q: 检测不到水印怎么办？
A:
1. 尝试调整 `detection_prompt` 提示词，使用更具体的描述
2. 增大 `max_bbox_percent` 参数值
3. 确保水印在图像中清晰可见
4. 对于视频，减小 `detection_skip` 值

### Q: 误检测了非水印区域？
A:
1. 减小 `max_bbox_percent` 参数值
2. 使用更精确的 `detection_prompt` 提示词
3. 检查输入图像质量

### Q: 处理速度慢？
A:
1. 确保使用GPU（CUDA）进行加速
2. 视频处理时增大 `detection_skip` 值（3-5）
3. 如果只需要快速处理，可以启用 `transparent` 模式
4. 检查系统内存是否充足

### Q: 视频处理后有闪烁？
A:
1. 减小 `detection_skip` 值以提高检测密度
2. 增加 `fade_in`/`fade_out` 值以扩展时间覆盖
3. 确保水印在视频中位置相对固定

### Q: 如何处理Sora2视频？
A: 使用视频节点，推荐参数：
```
detection_prompt: "Sora watermark"
detection_skip: 3
fade_in: 0.5
fade_out: 0.5
```

## 致谢

本项目基于以下开源项目：
- [WatermarkRemover-AI](https://github.com/D-Ogi/WatermarkRemover-AI) - 核心水印移除算法实现
- [Florence-2](https://huggingface.co/microsoft/Florence-2-large) - Microsoft视觉模型
- [LaMA](https://github.com/advimman/lama) - 图像修复模型
- [IOPaint](https://github.com/Sanster/IOPaint) - 图像修复工具包

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 更新日志

### v1.0.0
- 初始版本发布
- 支持Sora/Sora2图像水印移除
- 支持Sora/Sora2视频水印移除
- 集成Florence-2和LaMA模型
- 支持自定义检测提示词
- 实现两遍处理算法（稀疏检测 + 时间扩展）
- 支持fade-in/fade-out水印处理

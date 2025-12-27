# 快速开始指南

## 安装步骤

### 1. 克隆仓库
```bash
cd /path/to/ComfyUI/custom_nodes
git clone https://github.com/yourusername/ComfyUI-JM-Sora-Watermark-Remover.git
```

### 2. 安装依赖和模型
```bash
cd ComfyUI-JM-Sora-Watermark-Remover
python install.py
```

### 3. 重启ComfyUI
重启ComfyUI以加载新节点。

## 使用步骤

### 节点类型

本插件提供**两个节点**：

1. **Sora Watermark Remover (Image)** - 图像水印移除
2. **Sora Watermark Remover (Video)** - 视频水印移除

### 1. 在ComfyUI中找到节点
节点位置：`JM-Nodes → Video → Sora`

### 2. 基础工作流

#### 图像处理
```
Load Image → Sora Watermark Remover (Image) → Save Image
```

#### 视频处理
```
Load Video (VHS) → Sora Watermark Remover (Video) → Save Video (VHS)
```

### 3. 参数设置

#### 图像处理（推荐设置）

**检测Sora水印**:
- detection_prompt: `"Sora watermark"` 或 `"watermark"`
- max_bbox_percent: `10.0`
- transparent: `False`

**检测其他水印**:
- detection_prompt: 根据水印类型自定义（如 `"Getty Images"`, `"Runway watermark"`）
- max_bbox_percent: 根据水印大小调整（5-20）
- transparent: `False`（使用AI修复）或 `True`（快速处理）

#### 视频处理（推荐设置）

**Sora/Sora2视频水印**:
```
detection_prompt: "Sora watermark"
max_bbox_percent: 10.0
fps: 30.0 (根据你的视频实际帧率)
detection_skip: 3
fade_in: 0.5
fade_out: 0.5
transparent: False
```

**水印位置固定的视频（快速模式）**:
```
detection_skip: 5-10
fade_in: 0.0
fade_out: 0.0
```

**水印有渐变效果的视频**:
```
detection_skip: 3
fade_in: 1.0
fade_out: 1.0
```

## 模型下载说明

### 自动下载（首次使用）
- **Florence-2**: 首次使用时会自动从HuggingFace下载（约1GB）
- **LaMA**: 通过install.py安装时自动下载（约196MB）

### 手动下载LaMA模型
如果自动安装失败，可以手动下载：
```bash
mkdir -p ~/.cache/torch/hub/checkpoints
curl -L -o ~/.cache/torch/hub/checkpoints/big-lama.pt \
  https://github.com/Sanster/models/releases/download/add_big_lama/big-lama.pt
```

### 模型存储位置
- Florence-2: `~/.cache/huggingface/hub/`
- LaMA: `~/.cache/torch/hub/checkpoints/big-lama.pt`

## 常见使用场景

### 场景1: 移除Sora视频水印（完整视频）
```
工作流:
Load Video (VHS) → Sora Watermark Remover (Video) → Save Video (VHS)

参数设置:
- frames: 连接视频加载器输出
- detection_prompt: "Sora watermark"
- max_bbox_percent: 10.0
- fps: 30.0
- detection_skip: 3
- fade_in: 0.5
- fade_out: 0.5
- transparent: False
```

### 场景2: 移除Sora2视频水印（高质量）
```
参数设置:
- detection_prompt: "Sora watermark"
- detection_skip: 1 (每帧都检测，最准确)
- fade_in: 1.0
- fade_out: 1.0
- transparent: False
```

### 场景3: 快速处理视频（预览模式）
```
参数设置:
- detection_skip: 10 (大幅跳帧)
- fade_in: 0.0
- fade_out: 0.0
- transparent: True (跳过LaMA修复，更快)
```

### 场景4: 批量处理多张图片
```
工作流:
Load Images Batch → Sora Watermark Remover (Image) → Save Images
```

### 场景5: 移除图片水印
```
工作流:
Load Image → Sora Watermark Remover (Image) → Save Image

参数设置:
- detection_prompt: "watermark"
- max_bbox_percent: 10.0
- transparent: False
```

## 视频处理参数详解

### detection_skip（检测跳帧）
控制检测频率，影响速度和准确性：

- **1**: 每帧都检测
  - 优点：最准确，适合水印位置变化的视频
  - 缺点：最慢
  - 适用：高质量处理、水印位置不固定

- **3-5**: 推荐值
  - 优点：平衡速度和质量
  - 缺点：可能错过快速变化的水印
  - 适用：Sora/Sora2视频（水印位置相对固定）

- **7-10**: 快速模式
  - 优点：处理速度快
  - 缺点：准确性降低
  - 适用：水印完全固定、预览模式

### fade_in/fade_out（渐变处理）
扩展水印检测的时间范围：

- **0.0**: 无扩展
  - 适用：水印立即出现/消失，位置完全固定

- **0.5**: 轻微扩展
  - 适用：Sora视频标准设置

- **1.0-2.0**: 明显扩展
  - 适用：水印有明显的淡入淡出效果

### fps（帧率）
视频的帧率，用于计算fade-in/fade-out的帧数。

示例：
- 30fps，fade_in=0.5 → 向前扩展15帧
- 24fps，fade_in=1.0 → 向前扩展24帧

## 性能优化建议

### 视频处理性能优化

1. **GPU加速**（最重要）
   - 确保使用CUDA版本的PyTorch
   - 节点会自动检测并使用GPU

2. **调整检测密度**
   - Sora视频推荐：detection_skip = 3-5
   - 水印固定视频：detection_skip = 7-10

3. **使用透明模式快速预览**
   - 设置 transparent = True
   - 跳过LaMA修复，速度提升10倍

4. **分段处理长视频**
   - 将长视频分段
   - 分别处理后再合并

### 内存管理

- **图像批处理**: 建议每批次不超过10张（取决于GPU内存）
- **视频处理**: 视频帧会逐帧处理，内存占用相对稳定
- **推荐配置**:
  - 8GB RAM: 处理720p视频
  - 16GB RAM: 处理1080p视频
  - 24GB+ RAM: 处理4K视频

## 兼容性保证

本插件已针对ComfyUI环境优化：

✅ **使用ComfyUI已有依赖** - 不强制升级包版本
✅ **延迟加载** - 只在使用时才加载模型依赖
✅ **跨平台** - macOS/Linux/Windows均可运行
✅ **智能安装** - 自动检测并适配现有环境

## 故障排除

### 问题1: ComfyUI启动时报错导入失败
**原因**: 缺少依赖或版本不兼容

**解决方案**:
```bash
cd ComfyUI-JM-Sora-Watermark-Remover
python install.py
```

install.py会自动：
- 检查ComfyUI已有的依赖
- 只安装缺失的依赖
- 不强制升级现有包
- 下载所需模型

### 问题2: 节点使用时报错
**解决方案**:
1. 检查是否安装了所有依赖：`pip install -r requirements.txt`
2. 安装iopaint：`pip install iopaint --no-deps`
3. 重启ComfyUI

### 问题3: 模型下载失败
**解决方案**:
1. 检查网络连接
2. 手动下载LaMA模型：
   ```bash
   mkdir -p ~/.cache/torch/hub/checkpoints
   curl -L -o ~/.cache/torch/hub/checkpoints/big-lama.pt \
     https://github.com/Sanster/models/releases/download/add_big_lama/big-lama.pt
   ```
3. Florence-2需要访问HuggingFace，可能需要设置代理

### 问题4: CUDA内存不足
**解决方案**:
1. 减小输入图像/视频分辨率
2. 降低批处理数量
3. 增大detection_skip值
4. 使用CPU模式（性能会降低）

### 问题5: 视频检测不到水印
**解决方案**:
1. 调整detection_prompt，使用更具体的描述（如 `"Sora watermark"` 而不是 `"watermark"`）
2. 增大max_bbox_percent值
3. 减小detection_skip值（提高检测密度）
4. 确保视频中水印清晰可见

### 问题6: 视频处理后有闪烁
**解决方案**:
1. 减小detection_skip值（从5改为3或1）
2. 增加fade_in/fade_out值（从0.5改为1.0）
3. 检查水印是否在视频中位置相对固定

### 问题7: 处理速度太慢
**解决方案**:
1. 确保使用GPU（检查CUDA是否可用）
2. 增大detection_skip值（3→5→7）
3. 启用transparent模式进行快速预览
4. 检查系统内存是否充足

### 问题8: 误检测了非水印区域
**解决方案**:
1. 减小max_bbox_percent值（从10改为5）
2. 使用更精确的detection_prompt（如 `"Sora logo"` 而不是 `"watermark"`）
3. 检查输入视频质量

## 视频处理原理（简化说明）

### 为什么使用两遍处理？

传统方法：每帧都检测+修复 → 非常慢！

两遍处理方法：
1. **Pass 1**: 稀疏检测（只检测部分帧）
   - 例如：detection_skip=5，100帧只检测20次
   - 记录水印位置

2. **Pass 2**: 批量修复
   - 根据检测结果 + 时间扩展（fade_in/fade_out）
   - 对需要修复的帧应用LaMA
   - 无水印的帧直接保留

**结果**: 速度提升3-10倍，质量基本不变！

### 时间扩展示例

假设：
- 视频100帧，30fps
- detection_skip = 5
- fade_in = 0.5秒 (15帧)
- fade_out = 0.5秒 (15帧)

如果第10帧检测到水印：
- 实际处理范围：第0-30帧（10-15到10+5+15）
- 确保覆盖水印的淡入淡出

## ComfyUI工作流推荐

### 完整Sora视频处理工作流
```
[Load Video] → [Sora Video Watermark Remover] → [Save Video]
     ↓                      ↓
  frames            detection_prompt: "Sora watermark"
  (IMAGE)           detection_skip: 3
                    fade_in: 0.5
                    fade_out: 0.5
```

### 高级工作流（带预处理）
```
[Load Video] → [Video Quality Enhance] → [Sora Video Watermark Remover] → [Save Video]
```

### 批量图像处理工作流
```
[Batch Image Loader] → [Sora Image Watermark Remover] → [Batch Image Saver]
```

## 更多信息

详细文档请参考：[README.md](README.md)

## 技巧和最佳实践

### 检测提示词优化
- 通用检测：`"watermark"`
- Sora专用：`"Sora watermark"` 或 `"Sora logo"`
- 其他平台：`"Runway watermark"`, `"Pika logo"`
- 图库水印：`"Getty Images"`, `"Shutterstock watermark"`

### 视频处理最佳实践
1. 首次处理：使用默认参数测试几秒钟的片段
2. 调整参数：根据效果调整detection_skip和fade参数
3. 完整处理：使用优化后的参数处理完整视频
4. 质量检查：检查是否有闪烁或遗漏的水印

### 节省时间的建议
- 使用transparent模式快速预览检测效果
- 调整好参数后再用LaMA模式处理
- 对于长视频，先处理一小段验证效果

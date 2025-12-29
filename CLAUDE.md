# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个ComfyUI自定义节点插件,用于移除Sora/Sora2视频生成模型的水印。使用Florence-2模型进行AI智能检测,使用LaMA模型进行无痕修复。

## 核心架构

### 1. 节点系统

**两个主要节点类**:
- `SoraWatermarkRemover` (nodes.py:235-383): 图像水印移除节点
- `SoraVideoWatermarkRemover` (nodes.py:385-626): 视频水印移除节点

**节点注册** (__init__.py):
- 通过 `NODE_CLASS_MAPPINGS` 和 `NODE_DISPLAY_NAME_MAPPINGS` 注册节点
- 在ComfyUI中的分类路径: `JM-Nodes/Video/Sora`

### 2. AI模型集成

**Florence-2 (水印检测)**:
- 模型: `florence-community/Florence-2-large` (~1GB)
- 使用开放词汇检测 (`OPEN_VOCABULARY_DETECTION`) 任务
- 支持自定义检测提示词 (detection_prompt)
- 自动从HuggingFace下载到 `~/.cache/huggingface/hub/`
- **重要**: 需要 transformers>=4.38.1 (注意不是4.38.0), timm>=0.9.0, einops>=0.7.0
- **推荐**: transformers==4.57.3 或更高版本

**LaMA (图像修复)**:
- 模型: `big-lama.pt` (~196MB)
- 存储位置: `~/.cache/torch/hub/checkpoints/big-lama.pt`
- 通过IOPaint库加载和推理
- 需要通过install.py预先下载

### 3. 视频处理算法 - 两遍处理

**关键创新** (nodes.py:500-626):

**Pass 1 - 稀疏检测** (nodes.py:531-557):
- 每 `detection_skip` 帧进行一次检测
- 使用 `detect_only()` 函数只返回bbox,不创建mask
- 结果存储在 `detections` 字典中

**时间线扩展** (nodes.py:559-577):
- 根据 `fade_in`/`fade_out` 参数扩展检测时间范围
- 将检测结果映射到需要修复的帧 (`frame_masks`)
- 处理渐入渐出水印

**Pass 2 - 批量修复** (nodes.py:579-626):
- 只对 `frame_masks` 中的帧应用LaMA修复
- 无水印帧直接保留原始内容
- 显著提升处理效率

### 4. 依赖管理策略

**兼容性设计**:
- **延迟导入**: transformers和iopaint只在使用时导入,避免启动冲突 (nodes.py:12-16)
- **Monkey-patch**: 绕过peft版本检查以兼容ComfyUI旧版本 (nodes.py:66-109)
- **条件安装**: iopaint使用 `--no-deps` 安装避免依赖冲突 (install.py:78-87)
- **设备兼容**: 自动检测CUDA/MPS/CPU (nodes.py:242-248, 395-401)

## 常用命令

### 开发和测试

```bash
# 安装依赖和下载模型
python install.py

# 手动安装依赖
pip install -r requirements.txt
pip install iopaint --no-deps

# 手动下载LaMA模型
mkdir -p ~/.cache/torch/hub/checkpoints
curl -L -o ~/.cache/torch/hub/checkpoints/big-lama.pt \
  https://github.com/Sanster/models/releases/download/add_big_lama/big-lama.pt

# 检查包版本
python -c "import importlib.metadata; print(importlib.metadata.version('peft'))"
python -c "import importlib.metadata; print(importlib.metadata.version('diffusers'))"
```

### ComfyUI集成

```bash
# 安装到ComfyUI
cd /path/to/ComfyUI/custom_nodes
git clone <this-repo>
cd ComfyUI-JM-Sora-Watermark-Remover
python install.py

# 重启ComfyUI以加载节点
```

## 关键技术细节

### 设备选择逻辑

代码自动选择最优设备 (nodes.py:242-248):
1. CUDA (如果可用) - 最优
2. MPS (Apple Silicon) - 次优
3. CPU - 备选

**注意**: IOPaint/LaMA可能不支持MPS,会自动回退到CPU (nodes.py:112-114)

### 水印检测流程

1. 使用Florence-2进行开放词汇检测 (nodes.py:131-150)
2. 过滤大于 `max_bbox_percent` 的检测框,防止误检 (nodes.py:164-170)
3. 创建mask图像用于修复 (nodes.py:153-172)

### ComfyUI张量格式

**输入/输出张量格式** (nodes.py:328-335):
- 格式: `(B, H, W, C)` - 批次、高度、宽度、通道
- 数值范围: `[0, 1]` (float32)
- 需要转换到PIL/NumPy格式 (0-255 uint8) 进行处理

### 透明模式 vs LaMA修复

**透明模式** (transparent=True):
- 将水印区域设为透明 (nodes.py:221-232)
- 处理速度快~10倍
- 适合快速预览

**LaMA修复** (transparent=False):
- 使用AI修复水印区域 (nodes.py:200-218)
- 效果自然
- 处理较慢但质量高

### Bbox Padding (边界扩展)

**bbox_padding参数** (默认: 10像素):
- 在检测到的bbox四周扩展N个像素 (nodes.py:189-193, 772-776)
- 确保mask完全覆盖水印,防止边缘残留
- **适用场景**:
  - 水印检测bbox太小,没有完全覆盖水印
  - 水印边缘有模糊/半透明效果
  - 水印去除后还有淡淡的残留
- **推荐值**: 10-20像素 (取决于水印大小)
- **注意**: padding会自动限制在图像边界内,不会超出

## 代码修改指南

### 添加新的检测模型

1. 在 `load_models()` 中添加模型加载逻辑
2. 修改 `identify()` 函数支持新模型的推理格式
3. 更新 `INPUT_TYPES` 添加模型选择参数

### 修改视频处理算法

**关键函数**:
- `detect_only()` (nodes.py:175-197): 只检测不修复
- `process_image_with_lama()` (nodes.py:200-218): LaMA修复
- `remove_watermark()` in `SoraVideoWatermarkRemover` (nodes.py:500-626): 两遍处理主流程

### 添加新的ComfyUI节点

1. 创建新的节点类,继承自基类
2. 定义 `INPUT_TYPES` 类方法
3. 设置 `RETURN_TYPES`, `FUNCTION`, `CATEGORY`
4. 在 `NODE_CLASS_MAPPINGS` 和 `NODE_DISPLAY_NAME_MAPPINGS` 中注册

## 常见问题排查

### 水印没有被移除

**症状**: 视频处理后水印依然存在

**诊断工具**:
```bash
# 使用debug_detection.py测试检测是否工作
/path/to/comfyui/python debug_detection.py your_video.mp4
```

**常见原因**:
1. **检测问题**:
   - `detection_prompt` 不匹配(尝试: "Sora watermark", "watermark", "logo")
   - `max_bbox_percent` 太小(尝试增大到15.0或20.0)

2. **视频参数问题**:
   - `detection_skip` 太大导致跳过水印帧(减小到1-3)
   - `fade_in`/`fade_out` 未设置导致淡入淡出水印残留(设置为0.5-1.0)

3. **LaMA模型问题**:
   - 模型文件损坏或不存在(重新运行install.py)
   - `transparent=True` 导致使用白色填充而非AI修复(改为False)

**详细排查**: 参考 `TROUBLESHOOTING.md` 文件

### 依赖冲突

**症状**: ComfyUI启动时导入失败
**解决**: 运行 `python install.py`,它会检测现有依赖并只安装缺失的包

### 模型加载失败

**Florence-2导入失败** (`cannot import name 'Florence2ForConditionalGeneration'`):
- 原因: transformers版本过低或恰好是4.38.0
- 解决: 升级transformers到4.38.1+（推荐4.57.3）
  ```bash
  pip install --upgrade transformers==4.57.3 timm>=0.9.0
  ```
- 注意: transformers 4.38.0不包含Florence2，需要4.38.1或更高版本

**Florence-2下载失败**:
- 检查网络连接和HuggingFace访问
- 可能需要代理

**LaMA模型不存在**:
- 运行 `python install.py` 或手动下载
- 检查路径: `~/.cache/torch/hub/checkpoints/big-lama.pt`

### peft版本冲突

代码使用monkey-patch绕过版本检查 (nodes.py:66-109):
- 临时替换 `importlib.metadata.version` 函数
- 对peft返回假版本 "0.17.0"
- 使用后恢复原始函数

### CUDA内存不足

1. 减小输入分辨率
2. 减小批处理大小
3. 增大 `detection_skip` 值 (视频处理)
4. 使用CPU模式 (性能降低)

## 性能优化建议

### 视频处理优化

1. **调整检测密度**: `detection_skip=3-5` 平衡速度和质量
2. **使用GPU**: 确保CUDA可用
3. **透明模式预览**: 先用 `transparent=True` 验证检测,再用LaMA修复
4. **分段处理**: 长视频分段处理后合并

### 内存管理

- 图像批处理: 建议每批≤10张
- 视频处理: 逐帧处理,内存占用稳定
- 推荐配置:
  - 8GB RAM: 720p视频
  - 16GB RAM: 1080p视频
  - 24GB+ RAM: 4K视频

## 技术栈

- **PyTorch**: 深度学习框架 (CUDA/MPS/CPU支持)
- **Transformers**: HuggingFace模型库 (Florence-2)
- **IOPaint**: 图像修复工具包 (LaMA模型接口)
- **OpenCV**: 图像处理
- **Pillow**: 图像IO和操作
- **loguru**: 日志记录

## 代码风格约定

- 使用延迟导入避免启动时依赖冲突
- 所有AI模型相关导入放在函数内部
- 使用logger记录关键步骤和错误
- ComfyUI节点类使用大写驼峰命名
- 工具函数使用小写下划线命名

# 水印移除故障排查指南

> 💡 **快速诊断**：运行 `python diagnose.py` 自动检测所有问题！
>
> 📚 **查看工具说明**：[TOOLS_README.md](TOOLS_README.md) - 所有诊断工具的详细说明

## 🔍 诊断工具快速参考

| 问题类型 | 使用工具 | 命令 |
|---------|---------|------|
| 任何问题 | 综合诊断 | `python diagnose.py` |
| 依赖错误 | 自动修复 | `bash fix_dependencies.sh` |
| 水印未移除 | 检测测试 | `python debug_detection.py video.mp4` |
| Mac运行慢 | 性能检查 | `python check_performance.py` |
| 验证安装 | 快速测试 | `python test_installation.py` |

详细工具说明请查看：[TOOLS_README.md](TOOLS_README.md)

---

## 问题：视频处理后水印没有被移除

### 可能的原因和解决方案

#### 1. 检测参数设置不当

**问题**：`detection_prompt` 不匹配实际水印内容

**检查方法**：
```bash
# 使用诊断工具测试检测
/Users/jueming/miniconda/envs/comfyui/bin/python debug_detection.py your_video.mp4
```

**解决方案**：
尝试不同的检测提示词：
- `"watermark"` - 通用水印
- `"Sora watermark"` - Sora专用水印
- `"Sora logo"` - Sora logo
- `"logo"` - 通用logo检测

#### 2. max_bbox_percent 设置太小

**问题**：水印被检测到了，但因为面积过大被过滤掉了

**症状**：诊断工具显示"未检测到水印"

**解决方案**：
- 默认值：`10.0` (水印不超过图片10%面积)
- 如果水印较大，尝试：`15.0` 或 `20.0`
- 如果水印很小，尝试：`5.0`

#### 3. detection_skip 设置太大

**问题**：视频处理时跳过了太多帧，导致某些水印没有被检测到

**症状**：部分帧有水印残留

**解决方案**：
- 默认值：`1` (每帧都检测，最准确但最慢)
- 推荐值：`3-5` (适合Sora视频)
- 如果发现有残留，降低此值(例如从 `5` 改为 `3` 或 `1`)

#### 4. fade_in/fade_out 未设置

**问题**：水印有淡入淡出效果，但没有设置时间扩展参数

**症状**：视频开头或结尾有水印残留

**解决方案**：
- 对于Sora视频，建议设置：
  - `fade_in = 0.5` (秒)
  - `fade_out = 0.5` (秒)
- 如果水印淡入淡出明显，增加到 `1.0` 或 `2.0`

#### 5. LaMA 模型问题

**问题**：检测到了水印，但LaMA修复效果不好

**检查方法**：
```bash
# 检查LaMA模型是否存在
ls -lh ~/.cache/torch/hub/checkpoints/big-lama.pt
```

**解决方案**：
```bash
# 重新下载LaMA模型
rm ~/.cache/torch/hub/checkpoints/big-lama.pt
/Users/jueming/miniconda/envs/comfyui/bin/python install.py
```

#### 6. ComfyUI 张量格式问题

**问题**：可能是ComfyUI的IMAGE tensor处理有问题

**检查步骤**：
1. 确认输入是视频帧序列(IMAGE批次，形状为 B×H×W×C)
2. 确认fps参数设置正确
3. 检查ComfyUI控制台是否有错误信息

## 使用诊断工具

### 快速测试

对单个图片或视频进行检测测试：

```bash
# 基础测试(使用默认参数)
/Users/jueming/miniconda/envs/comfyui/bin/python debug_detection.py your_video.mp4

# 自定义检测提示词
/Users/jueming/miniconda/envs/comfyui/bin/python debug_detection.py your_video.mp4 "Sora watermark"

# 自定义最大面积百分比
/Users/jueming/miniconda/envs/comfyui/bin/python debug_detection.py your_video.mp4 "watermark" 15.0
```

### 诊断输出解读

**成功检测示例**：
```
检测结果: 找到 1 个水印区域

水印 1:
  位置: x1=1650, y1=950, x2=1750, y2=1000
  大小: 100 x 50 像素
  占比: 0.26%

✓ 已保存标注图片到: your_video_detected.png
```

**未检测到水印**：
```
检测结果: 找到 0 个水印区域

⚠️  未检测到水印！

可能的原因:
1. detection_prompt 不匹配水印内容
2. max_bbox_percent 设置太小
3. 图片中确实没有水印
```

## 代码对比：参考项目 vs ComfyUI版本

### 关键差异

#### 1. detect_only 返回格式

**参考项目** (WatermarkRemover-AI):
```python
# 返回详细信息的字典列表
return [{"bbox": [x1,y1,x2,y2], "area_percent": float, "accepted": bool}, ...]

# 使用时需要过滤
accepted_bboxes = [b["bbox"] for b in bboxes if b["accepted"]]
```

**ComfyUI版本**:
```python
# 直接返回accepted的bbox列表
if accepted:
    results.append([x1, y1, x2, y2])
return results

# 使用时直接用
detections[frame_idx] = bboxes
```

**结论**：逻辑等价，不应该影响结果。

#### 2. 视频处理方式

**参考项目**：
- 使用cv2.VideoWriter写入视频文件
- 使用FFmpeg合并音频

**ComfyUI版本**：
- 处理IMAGE tensor批次
- 返回处理后的tensor由ComfyUI保存

**结论**：实现方式不同，但核心水印移除逻辑相同。

## 推荐的排查步骤

### Step 1: 验证检测是否工作

```bash
/Users/jueming/miniconda/envs/comfyui/bin/python debug_detection.py your_video.mp4
```

- 如果**检测到水印**：说明Florence-2工作正常，继续Step 2
- 如果**未检测到水印**：调整 `detection_prompt` 和 `max_bbox_percent`

### Step 2: 检查LaMA模型

```bash
# 验证模型文件存在
ls -lh ~/.cache/torch/hub/checkpoints/big-lama.pt

# 如果文件不存在或大小不对(应该约196MB)，重新下载
/Users/jueming/miniconda/envs/comfyui/bin/python install.py
```

### Step 3: 调整ComfyUI节点参数

在ComfyUI中，调整 `Sora Watermark Remover (Video)` 节点的参数：

**推荐设置**：
```
detection_prompt: "Sora watermark"  # 或 "watermark"
max_bbox_percent: 10.0              # 如果检测不到，增加到15.0
fps: 30.0                           # 根据实际视频帧率
detection_skip: 3                   # 如果有残留，减小到1
fade_in: 0.5                        # 处理淡入水印
fade_out: 0.5                       # 处理淡出水印
transparent: False                  # 使用LaMA修复
```

### Step 4: 查看ComfyUI日志

检查ComfyUI控制台输出，寻找类似信息：
```
Pass 1: Detecting watermarks...
Pass 1 complete: found watermarks in X detection points
Timeline expanded: Y frames will have inpainting applied
Pass 2: Applying inpainting...
```

- 如果 `X = 0`：说明没检测到任何水印，返回Step 1
- 如果 `Y = 0`：说明检测到了但timeline expansion有问题
- 如果 `Y > 0` 但水印还在：可能是LaMA修复效果不好

## 常见问题FAQ

### Q: 为什么诊断工具检测到了水印，但ComfyUI处理后还有水印？

A: 可能原因：
1. LaMA模型加载失败或文件损坏
2. `transparent` 模式被设置为 `True`(这会用白色填充而不是AI修复)
3. 显存不足导致处理失败(检查ComfyUI日志)

### Q: 如何知道检测和修复都正常工作？

A: 检查ComfyUI控制台日志：
```
Loading Florence-2 model...
Florence-2 model loaded successfully
Loading LaMA model...
LaMA model loaded successfully
Pass 1: Detecting watermarks...
Pass 1 complete: found watermarks in 10 detection points
Timeline expanded: 50 frames will have inpainting applied
Pass 2: Applying inpainting...
Video processing complete: 100 frames processed
```

### Q: 能否先测试单张图片？

A: 可以！使用 `Sora Watermark Remover (Image)` 节点：
1. 从视频中提取一帧
2. 使用Image节点处理
3. 如果图片处理成功，说明检测和LaMA都正常
4. 如果图片处理也失败，说明是检测或LaMA的问题

## 联系支持

如果以上步骤都无法解决问题，请提供：
1. 诊断工具的完整输出
2. ComfyUI控制台的错误日志
3. 节点参数截图
4. 示例图片/视频(如果可以分享)

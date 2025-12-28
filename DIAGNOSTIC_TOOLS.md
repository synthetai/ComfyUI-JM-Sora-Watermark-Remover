# 诊断工具完整清单

本文档列出了项目中所有可用的诊断和修复工具。

## 📋 文件清单

### 🔍 诊断脚本

| 文件 | 类型 | 用途 | 优先级 |
|------|------|------|--------|
| `diagnose.py` | Python | 综合环境诊断（检查所有依赖、模型、GPU） | ⭐⭐⭐⭐⭐ |
| `test_installation.py` | Python | 快速安装验证（简化版诊断） | ⭐⭐⭐⭐ |
| `debug_detection.py` | Python | 水印检测测试（生成标注图片） | ⭐⭐⭐⭐ |
| `check_performance.py` | Python | Mac M1性能检查（Rosetta检测） | ⭐⭐⭐ |
| `check_devices.py` | Python | 设备检查（Florence-2 vs LaMA设备） | ⭐⭐ |

### 🔧 修复脚本

| 文件 | 类型 | 用途 | 优先级 |
|------|------|------|--------|
| `fix_dependencies.sh` | Bash | 自动修复所有依赖问题 | ⭐⭐⭐⭐⭐ |
| `install.py` | Python | 标准安装脚本 | ⭐⭐⭐⭐ |

### 📚 文档

| 文件 | 用途 | 适合人群 |
|------|------|----------|
| `QUICK_START.md` | 快速开始指南，常见问题速查 | 新用户 |
| `TROUBLESHOOTING.md` | 详细故障排查指南 | 遇到问题的用户 |
| `TOOLS_README.md` | 诊断工具详细说明 | 所有用户 |
| `CLAUDE.md` | 项目架构和开发文档 | 开发者 |
| `README.md` | 项目主文档 | 所有用户 |

## 🚀 使用流程

### 场景1：首次安装

```bash
# 步骤1: 克隆仓库
cd /path/to/ComfyUI/custom_nodes
git clone <repo-url> ComfyUI-JM-Sora-Watermark-Remover

# 步骤2: 安装
cd ComfyUI-JM-Sora-Watermark-Remover
python install.py

# 步骤3: 验证
python test_installation.py
# 或完整诊断
python diagnose.py

# 步骤4: 重启ComfyUI
```

### 场景2：遇到错误

```bash
# 步骤1: 运行诊断（最重要！）
python diagnose.py

# 步骤2: 查看输出，按建议修复
# 如果是依赖问题：
bash fix_dependencies.sh

# 步骤3: 再次验证
python diagnose.py
```

### 场景3：水印没被移除

```bash
# 步骤1: 测试检测
python debug_detection.py your_video.mp4

# 步骤2: 查看生成的 *_detected.png
# - 如果有绿色框：检测成功，问题在修复
# - 如果没有框：检测失败，需要调整参数

# 步骤3: 尝试不同参数
python debug_detection.py your_video.mp4 "Sora watermark"
python debug_detection.py your_video.mp4 "Sora watermark" 15.0

# 步骤4: 在ComfyUI中使用成功的参数
```

### 场景4：Mac运行慢

```bash
# 步骤1: 检查性能
python check_performance.py

# 步骤2: 如果显示Rosetta 2
# 选项A: 安装ARM64 Python（最佳）
# 选项B: 优化参数 detection_skip=5

# 步骤3: 验证设备使用
python check_devices.py
```

## 📊 问题诊断流程图

```
遇到问题
    |
    v
运行 diagnose.py
    |
    +-- 依赖问题? --> bash fix_dependencies.sh
    |
    +-- 水印问题? --> python debug_detection.py
    |
    +-- 性能问题? --> python check_performance.py
    |
    +-- 验证修复 --> python test_installation.py
    |
    v
重启ComfyUI
```

## 🎯 常见错误 → 工具映射

| 错误信息 | 使用工具 | 说明 |
|---------|---------|------|
| `cannot import Florence2...` | `diagnose.py` → `fix_dependencies.sh` | transformers版本问题 |
| `LaMA model not found` | `diagnose.py` → `install.py` | 模型未下载 |
| 水印没被移除 | `debug_detection.py` | 检测或参数问题 |
| 处理速度慢 (Mac) | `check_performance.py` | Rosetta 2问题 |
| 任何导入错误 | `diagnose.py` → `fix_dependencies.sh` | 依赖问题 |

## 💡 最佳实践

### ✅ 推荐

1. **首次安装后**：运行 `python test_installation.py`
2. **遇到任何错误**：运行 `python diagnose.py`
3. **报告问题前**：附上 `diagnose.py` 的完整输出
4. **升级依赖后**：运行 `python diagnose.py` 验证

### ❌ 不推荐

1. ❌ 不运行诊断就手动修改代码
2. ❌ 忽略诊断脚本的警告
3. ❌ 同时运行多个修复脚本
4. ❌ 报告问题时不提供诊断信息

## 📝 每个工具的详细说明

### diagnose.py

**功能**：
- 系统和Python架构检查
- 所有依赖版本检查（包括transformers 4.38.0特殊检查）
- Florence-2导入测试
- LaMA模型文件检查
- GPU/MPS加速检测和性能测试
- 自动生成针对性的修复建议

**输出**：
- 分类的问题列表（严重/高/中）
- 逐步修复指令
- 具体的命令示例

**何时使用**：
- 任何时候有问题
- 安装验证
- 报告问题前

---

### test_installation.py

**功能**：
- 快速检查关键组件
- 版本验证
- 模型文件检查
- GPU支持检查

**输出**：
- 简洁的通过/失败状态
- 下一步建议

**何时使用**：
- 快速验证安装
- 不需要详细诊断时

---

### debug_detection.py

**功能**：
- 加载图片/视频帧
- 运行Florence-2检测
- 生成标注图片
- 输出检测详情

**输出**：
- 控制台：检测数量、位置、大小
- 文件：`*_detected.png`（带绿色框标注）

**何时使用**：
- 水印没被移除
- 测试不同的 detection_prompt
- 验证检测是否正常

---

### check_performance.py

**功能**：
- 检测Python架构（ARM64 vs x86_64）
- MPS性能基准测试
- 与CPU性能对比

**输出**：
- 架构类型
- MPS加速比（如 3.5x 或 0.67x）
- 性能建议

**何时使用**：
- Mac用户处理慢
- 怀疑Rosetta 2问题
- 验证MPS是否正常工作

---

### fix_dependencies.sh

**功能**：
- 自动检测transformers版本
- 升级到4.57.3（如果需要）
- 安装所有依赖
- 下载LaMA模型
- 验证安装

**输出**：
- 详细的安装日志
- 每步的成功/失败状态
- 最终验证结果

**何时使用**：
- diagnose.py报告依赖问题
- 需要重新安装所有依赖
- 手动安装失败

---

## 🆘 故障排除

如果诊断工具本身失败：

1. **Python版本问题**：
   ```bash
   python --version  # 应该 >= 3.10
   ```

2. **缺少packaging模块**：
   ```bash
   pip install packaging
   ```

3. **权限问题**：
   ```bash
   chmod +x fix_dependencies.sh
   bash fix_dependencies.sh
   ```

4. **找不到pip**：
   ```bash
   python -m pip install --upgrade pip
   ```

## 🔗 相关链接

- 工具详细说明：[TOOLS_README.md](TOOLS_README.md)
- 快速开始：[QUICK_START.md](QUICK_START.md)
- 故障排查：[TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- 开发文档：[CLAUDE.md](CLAUDE.md)

---

**记住**：`python diagnose.py` 是您解决问题的第一步！

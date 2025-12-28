# 📚 完整文档索引

## 🎯 快速导航

**遇到问题？** → [QUICK_START.md](QUICK_START.md) → `python diagnose.py`

**需要深入了解？** → 查看下面的分类文档

---

## 📖 用户文档（按使用顺序）

### 1. 新用户入门
- **[README.md](README.md)** - 项目介绍、功能特性、基本安装
  - 快速了解项目
  - 安装方法
  - 基本使用说明

### 2. 快速开始
- **[QUICK_START.md](QUICK_START.md)** ⭐ 新手必读
  - 常见问题速查表
  - 快速修复命令
  - 完整安装流程
  - 工作流示例

### 3. 遇到问题时
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - 详细故障排查
  - 水印移除问题分析
  - 参数调优指南
  - 性能优化方案
  - 代码对比分析

### 4. 工具使用
- **[TOOLS_README.md](TOOLS_README.md)** - 诊断工具详细说明
  - 每个工具的功能
  - 使用方法
  - 最佳实践

- **[DIAGNOSTIC_TOOLS.md](DIAGNOSTIC_TOOLS.md)** - 工具清单和流程
  - 完整工具列表
  - 使用流程图
  - 问题→工具映射

---

## 🔧 诊断和修复工具

### Python脚本

| 工具 | 功能 | 使用 | 优先级 |
|------|------|------|--------|
| **diagnose.py** | 综合环境诊断 | `python diagnose.py` | ⭐⭐⭐⭐⭐ |
| **test_installation.py** | 快速安装验证 | `python test_installation.py` | ⭐⭐⭐⭐ |
| **debug_detection.py** | 水印检测测试 | `python debug_detection.py video.mp4` | ⭐⭐⭐⭐ |
| **check_performance.py** | Mac性能检查 | `python check_performance.py` | ⭐⭐⭐ (Mac) |
| **check_devices.py** | 设备检查 | `python check_devices.py` | ⭐⭐ |

### Bash脚本

| 工具 | 功能 | 使用 | 优先级 |
|------|------|------|--------|
| **fix_dependencies.sh** | 自动修复依赖 | `bash fix_dependencies.sh` | ⭐⭐⭐⭐⭐ |

### 安装脚本

| 工具 | 功能 | 使用 |
|------|------|------|
| **install.py** | 标准安装 | `python install.py` |

---

## 💻 开发者文档

- **[CLAUDE.md](CLAUDE.md)** - 项目架构和开发指南
  - 核心架构说明
  - 两遍处理算法详解
  - 常用命令
  - 代码修改指南
  - 技术栈说明

---

## 🗂️ 文件组织

```
ComfyUI-JM-Sora-Watermark-Remover/
├── 📄 核心代码
│   ├── __init__.py          # 节点注册
│   ├── nodes.py             # 主要节点实现
│   └── requirements.txt     # Python依赖
│
├── 📚 用户文档
│   ├── README.md            # 项目主文档 ⭐
│   ├── QUICK_START.md       # 快速开始 ⭐⭐⭐
│   ├── TROUBLESHOOTING.md   # 故障排查
│   ├── TOOLS_README.md      # 工具说明
│   ├── DIAGNOSTIC_TOOLS.md  # 工具清单
│   └── INDEX.md             # 本文档
│
├── 💻 开发文档
│   └── CLAUDE.md            # 架构文档
│
├── 🔍 诊断工具
│   ├── diagnose.py          # 综合诊断 ⭐⭐⭐
│   ├── test_installation.py # 快速验证
│   ├── debug_detection.py   # 检测测试
│   ├── check_performance.py # 性能检查 (Mac)
│   └── check_devices.py     # 设备检查
│
├── 🔧 修复工具
│   ├── fix_dependencies.sh  # 自动修复 ⭐⭐⭐
│   └── install.py           # 标准安装
│
└── 📖 项目元数据
    ├── LICENSE
    └── .gitignore
```

---

## 🚀 推荐使用路径

### 路径A：新用户首次安装

```
1. README.md (了解项目)
   ↓
2. 运行: python install.py
   ↓
3. 运行: python test_installation.py
   ↓
4. QUICK_START.md (学习使用)
   ↓
5. 重启ComfyUI并测试
```

### 路径B：遇到问题

```
1. 运行: python diagnose.py ⭐ (最重要!)
   ↓
2. QUICK_START.md (查看问题速查表)
   ↓
3. 运行: bash fix_dependencies.sh (如果是依赖问题)
   或
   运行: python debug_detection.py (如果是检测问题)
   ↓
4. TROUBLESHOOTING.md (深入了解)
   ↓
5. 再次验证: python diagnose.py
```

### 路径C：性能优化 (Mac M1)

```
1. 运行: python check_performance.py
   ↓
2. TROUBLESHOOTING.md (性能优化章节)
   ↓
3. 根据建议优化或安装ARM64 Python
```

### 路径D：深入开发

```
1. CLAUDE.md (了解架构)
   ↓
2. 阅读 nodes.py 核心代码
   ↓
3. 参考 TROUBLESHOOTING.md 中的代码对比
   ↓
4. 使用诊断工具验证修改
```

---

## 📊 文档对比表

| 文档 | 长度 | 难度 | 适合场景 | 必读程度 |
|------|------|------|----------|----------|
| README.md | 中 | 易 | 初次了解项目 | ⭐⭐⭐⭐ |
| QUICK_START.md | 中 | 易 | 快速解决问题 | ⭐⭐⭐⭐⭐ |
| TROUBLESHOOTING.md | 长 | 中 | 深入排查 | ⭐⭐⭐⭐ |
| TOOLS_README.md | 中 | 易 | 了解工具 | ⭐⭐⭐ |
| DIAGNOSTIC_TOOLS.md | 中 | 易 | 工具参考 | ⭐⭐⭐ |
| CLAUDE.md | 长 | 难 | 开发/调试 | ⭐⭐⭐ (开发者) |
| INDEX.md | 短 | 易 | 导航 | ⭐⭐ |

---

## 🔍 按问题类型查找

### 安装问题
- 主文档：QUICK_START.md → "完整安装流程"
- 工具：`python diagnose.py` → `bash fix_dependencies.sh`
- 详细：TROUBLESHOOTING.md → "依赖冲突"

### 导入错误
- 快速：QUICK_START.md → "cannot import Florence2"
- 工具：`python diagnose.py`
- 详细：CLAUDE.md → "模型加载失败"

### 水印未移除
- 快速：QUICK_START.md → "水印没有被移除"
- 工具：`python debug_detection.py video.mp4`
- 详细：TROUBLESHOOTING.md → "水印移除问题"

### 运行速度慢
- 快速：QUICK_START.md → "处理速度很慢"
- 工具：`python check_performance.py` (Mac)
- 详细：TROUBLESHOOTING.md → "性能优化"

### 参数优化
- 快速：QUICK_START.md → "工作流示例"
- 详细：README.md → "参数调优建议"
- 深入：TROUBLESHOOTING.md → "检测参数优化"

---

## 💡 使用技巧

### 快速查找答案

1. **搜索关键词**：在 QUICK_START.md 中用 Ctrl+F 搜索错误信息
2. **查看工具表**：在 TOOLS_README.md 中找到合适的工具
3. **运行诊断**：`python diagnose.py` 会给出具体建议

### 报告问题

提供以下信息可以更快获得帮助：

```bash
# 1. 诊断输出
python diagnose.py > diagnosis.txt

# 2. 系统信息
python -c "import sys, platform; print(f'OS: {platform.platform()}\nPython: {sys.version}')"

# 3. 如果是检测问题
python debug_detection.py your_video.mp4
# 附上生成的 *_detected.png
```

### 学习路径

1. **入门级**：README.md → QUICK_START.md
2. **进阶级**：TROUBLESHOOTING.md → TOOLS_README.md
3. **专家级**：CLAUDE.md → 源代码

---

## 🔄 文档更新

本文档索引会随着项目更新而更新。

**最后更新**：2025-12-27

**版本**：v1.0

---

## 🆘 找不到答案？

1. ✅ 运行 `python diagnose.py`
2. ✅ 查看 [QUICK_START.md](QUICK_START.md)
3. ✅ 查看 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
4. ✅ 提交 Issue（附上诊断输出）

---

**记住**：90%的问题都能通过阅读 QUICK_START.md 和运行 `python diagnose.py` 解决！

#!/bin/bash

# ComfyUI-JM-Sora-Watermark-Remover 依赖修复脚本
# 适用于 Mac 和 Linux
# 用法: bash fix_dependencies.sh

set -e  # 遇到错误立即退出

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ComfyUI-JM-Sora-Watermark-Remover 依赖修复脚本             ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# 检测Python
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "❌ 错误: 未找到Python"
    exit 1
fi

echo "✓ 使用Python: $($PYTHON --version)"
echo "✓ Python路径: $(which $PYTHON)"
echo ""

# 检测pip
if command -v pip3 &> /dev/null; then
    PIP=pip3
elif command -v pip &> /dev/null; then
    PIP=pip
else
    echo "❌ 错误: 未找到pip"
    exit 1
fi

echo "════════════════════════════════════════════════════════════════"
echo "  步骤 1/5: 检查当前环境"
echo "════════════════════════════════════════════════════════════════"

# 检查transformers版本
echo "检查transformers版本..."
TRANS_VERSION=$($PYTHON -c "import transformers; print(transformers.__version__)" 2>/dev/null || echo "未安装")
echo "当前版本: $TRANS_VERSION"

if [ "$TRANS_VERSION" = "4.38.0" ]; then
    echo "⚠️  警告: transformers 4.38.0 不包含Florence2!"
    echo "   必须升级到 4.38.1 或更高版本"
    NEED_UPGRADE=1
elif [ "$TRANS_VERSION" = "未安装" ]; then
    echo "⚠️  transformers 未安装"
    NEED_UPGRADE=1
else
    # 版本比较
    REQUIRED="4.38.1"
    if $PYTHON -c "from packaging import version; exit(0 if version.parse('$TRANS_VERSION') >= version.parse('$REQUIRED') else 1)" 2>/dev/null; then
        echo "✓ transformers版本满足要求 (>= 4.38.1)"
        NEED_UPGRADE=0
    else
        echo "⚠️  transformers版本过低 (需要 >= 4.38.1)"
        NEED_UPGRADE=1
    fi
fi

echo ""

echo "════════════════════════════════════════════════════════════════"
echo "  步骤 2/5: 升级核心依赖"
echo "════════════════════════════════════════════════════════════════"

if [ $NEED_UPGRADE -eq 1 ]; then
    echo "升级 transformers 到 4.57.3..."
    $PIP install --upgrade transformers==4.57.3
    echo "✓ transformers 升级完成"
else
    echo "跳过 transformers 升级（已是最新版本）"
fi

echo ""
echo "升级其他核心依赖..."
$PIP install --upgrade timm>=0.9.0 einops>=0.7.0
echo "✓ timm 和 einops 升级完成"

echo ""

echo "════════════════════════════════════════════════════════════════"
echo "  步骤 3/5: 安装其他依赖"
echo "════════════════════════════════════════════════════════════════"

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    echo "从 requirements.txt 安装依赖..."
    $PIP install -r "$SCRIPT_DIR/requirements.txt"
    echo "✓ 基础依赖安装完成"
else
    echo "⚠️  未找到 requirements.txt，跳过"
fi

echo ""

echo "════════════════════════════════════════════════════════════════"
echo "  步骤 4/5: 安装 IOPaint"
echo "════════════════════════════════════════════════════════════════"

echo "安装 iopaint (使用 --no-deps 避免依赖冲突)..."
$PIP install iopaint --no-deps
echo "✓ iopaint 安装完成"

echo ""

echo "════════════════════════════════════════════════════════════════"
echo "  步骤 5/5: 下载模型"
echo "════════════════════════════════════════════════════════════════"

if [ -f "$SCRIPT_DIR/install.py" ]; then
    echo "运行 install.py 下载LaMA模型..."
    $PYTHON "$SCRIPT_DIR/install.py"
else
    echo "⚠️  未找到 install.py，手动下载LaMA模型..."

    # 手动下载LaMA模型
    LAMA_DIR="$HOME/.cache/torch/hub/checkpoints"
    LAMA_FILE="$LAMA_DIR/big-lama.pt"
    LAMA_URL="https://github.com/Sanster/models/releases/download/add_big_lama/big-lama.pt"

    if [ -f "$LAMA_FILE" ]; then
        echo "✓ LaMA模型已存在: $LAMA_FILE"
    else
        echo "下载LaMA模型 (~196MB)..."
        mkdir -p "$LAMA_DIR"

        if command -v curl &> /dev/null; then
            curl -L -o "$LAMA_FILE" "$LAMA_URL"
        elif command -v wget &> /dev/null; then
            wget -O "$LAMA_FILE" "$LAMA_URL"
        else
            echo "❌ 错误: 需要 curl 或 wget 来下载模型"
            echo "请手动下载:"
            echo "  mkdir -p $LAMA_DIR"
            echo "  # 下载 $LAMA_URL"
            echo "  # 保存到 $LAMA_FILE"
            exit 1
        fi

        echo "✓ LaMA模型下载完成"
    fi
fi

echo ""

echo "════════════════════════════════════════════════════════════════"
echo "  验证安装"
echo "════════════════════════════════════════════════════════════════"

echo ""
echo "验证 Florence-2..."
if $PYTHON -c "from transformers import Florence2ForConditionalGeneration; print('✓ Florence-2 可以导入')" 2>/dev/null; then
    echo "✓ Florence-2 验证通过"
else
    echo "❌ Florence-2 验证失败"
    exit 1
fi

echo ""
echo "验证 IOPaint..."
if $PYTHON -c "from iopaint.model_manager import ModelManager; print('✓ IOPaint 可以导入')" 2>/dev/null; then
    echo "✓ IOPaint 验证通过"
else
    echo "❌ IOPaint 验证失败"
    exit 1
fi

echo ""
echo "验证 LaMA 模型文件..."
LAMA_FILE="$HOME/.cache/torch/hub/checkpoints/big-lama.pt"
if [ -f "$LAMA_FILE" ]; then
    SIZE=$(du -m "$LAMA_FILE" | cut -f1)
    if [ $SIZE -gt 190 ] && [ $SIZE -lt 200 ]; then
        echo "✓ LaMA模型文件存在且大小正常 (${SIZE}MB)"
    else
        echo "⚠️  LaMA模型文件大小异常 (${SIZE}MB，应该约196MB)"
    fi
else
    echo "❌ LaMA模型文件不存在: $LAMA_FILE"
    exit 1
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  🎉 修复完成！"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "已安装/升级的包:"
echo "  ✓ transformers >= 4.38.1"
echo "  ✓ timm >= 0.9.0"
echo "  ✓ einops >= 0.7.0"
echo "  ✓ iopaint"
echo "  ✓ LaMA 模型"
echo ""
echo "下一步:"
echo "  1. 重启 ComfyUI"
echo "  2. 运行诊断脚本验证: python diagnose.py"
echo "  3. 在ComfyUI中测试水印移除节点"
echo ""

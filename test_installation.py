#!/usr/bin/env python3
"""
快速安装验证脚本

用法：python test_installation.py

这是一个简化版的诊断脚本，只检查关键组件是否正常工作。
如需完整诊断，请运行：python diagnose.py
"""

import sys

def test_import(module_name, from_module=None):
    """测试模块导入"""
    try:
        if from_module:
            exec(f"from {module_name} import {from_module}")
            print(f"  ✅ {module_name}.{from_module}")
        else:
            __import__(module_name)
            print(f"  ✅ {module_name}")
        return True
    except ImportError as e:
        print(f"  ❌ {module_name}: {e}")
        return False

def main():
    print("="*60)
    print("  快速安装验证")
    print("="*60)
    print()

    all_ok = True

    # 基础依赖
    print("检查基础依赖...")
    all_ok &= test_import("torch")
    all_ok &= test_import("numpy")
    all_ok &= test_import("PIL", "Image")
    all_ok &= test_import("cv2")
    print()

    # 关键依赖
    print("检查关键依赖...")
    all_ok &= test_import("transformers")
    all_ok &= test_import("timm")
    all_ok &= test_import("einops")
    all_ok &= test_import("loguru")
    print()

    # 版本检查
    print("检查版本...")
    try:
        import transformers
        version = transformers.__version__
        print(f"  transformers: {version}")
        if version == "4.38.0":
            print(f"  ⚠️  版本4.38.0不包含Florence2，需要升级到4.38.1+")
            all_ok = False
        elif version < "4.38.1":
            print(f"  ❌ 版本过低，需要>=4.38.1")
            all_ok = False
        else:
            print(f"  ✅ 版本满足要求")
    except:
        print(f"  ❌ 无法检查transformers版本")
        all_ok = False
    print()

    # 模型导入
    print("检查模型导入...")
    all_ok &= test_import("transformers", "Florence2ForConditionalGeneration")
    all_ok &= test_import("transformers", "AutoProcessor")
    all_ok &= test_import("iopaint.model_manager", "ModelManager")
    print()

    # 模型文件
    print("检查模型文件...")
    from pathlib import Path
    lama_path = Path.home() / ".cache" / "torch" / "hub" / "checkpoints" / "big-lama.pt"
    if lama_path.exists():
        size_mb = lama_path.stat().st_size / (1024 * 1024)
        if 190 < size_mb < 200:
            print(f"  ✅ LaMA模型: {size_mb:.1f}MB")
        else:
            print(f"  ⚠️  LaMA模型大小异常: {size_mb:.1f}MB (应约196MB)")
            all_ok = False
    else:
        print(f"  ❌ LaMA模型未找到: {lama_path}")
        all_ok = False
    print()

    # GPU检查
    print("检查GPU支持...")
    try:
        import torch
        if torch.cuda.is_available():
            print(f"  ✅ CUDA可用: {torch.version.cuda}")
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            print(f"  ✅ MPS (Apple GPU) 可用")
        else:
            print(f"  ⚠️  仅CPU可用（处理会较慢）")
    except:
        print(f"  ❌ 无法检查GPU")
    print()

    # 结果
    print("="*60)
    if all_ok:
        print("  🎉 安装验证通过！")
        print()
        print("  下一步:")
        print("    1. 重启 ComfyUI")
        print("    2. 在节点菜单中找到: JM-Nodes → Video → Sora")
        print("    3. 使用 Sora Watermark Remover 节点")
    else:
        print("  ⚠️  发现一些问题")
        print()
        print("  建议:")
        print("    1. 运行完整诊断: python diagnose.py")
        print("    2. 运行自动修复: bash fix_dependencies.sh")
        print("    3. 查看文档: QUICK_START.md")
    print("="*60)

    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())

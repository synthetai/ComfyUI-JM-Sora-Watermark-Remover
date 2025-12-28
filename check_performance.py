#!/usr/bin/env python3
"""检查当前环境的架构和性能"""
import platform
import sys
import torch

print("=== 系统和Python架构检查 ===\n")

# 系统架构
print(f"系统架构: {platform.machine()}")
print(f"系统版本: {platform.platform()}")

# Python架构
print(f"\nPython版本: {sys.version}")
print(f"Python路径: {sys.executable}")

# 使用platform检测
import subprocess
result = subprocess.run(['file', sys.executable], capture_output=True, text=True)
if 'arm64' in result.stdout:
    print("✅ Python架构: ARM64 (原生)")
elif 'x86_64' in result.stdout:
    print("❌ Python架构: Intel x86_64 (Rosetta 2转译)")
    print("   ⚠️  性能损失: ~20-30%")
    print("   ⚠️  建议安装ARM64版本的Conda/Miniforge")
else:
    print(f"未知架构: {result.stdout}")

# PyTorch和MPS
print(f"\n=== PyTorch配置 ===\n")
print(f"PyTorch版本: {torch.__version__}")
print(f"MPS可用: {torch.backends.mps.is_available()}")
print(f"MPS已构建: {torch.backends.mps.is_built()}")

# 性能测试
if torch.backends.mps.is_available():
    print("\n=== MPS性能测试 ===\n")
    try:
        import time
        # 创建测试张量
        size = 1000
        cpu_tensor = torch.randn(size, size)
        mps_tensor = cpu_tensor.to('mps')

        # CPU测试
        start = time.time()
        for _ in range(10):
            _ = torch.matmul(cpu_tensor, cpu_tensor)
        cpu_time = time.time() - start

        # MPS测试
        start = time.time()
        for _ in range(10):
            _ = torch.matmul(mps_tensor, mps_tensor)
        torch.mps.synchronize()  # 等待GPU完成
        mps_time = time.time() - start

        print(f"CPU时间: {cpu_time:.4f}秒")
        print(f"MPS时间: {mps_time:.4f}秒")
        print(f"加速比: {cpu_time/mps_time:.2f}x")

        if mps_time >= cpu_time:
            print("\n⚠️  警告：MPS没有比CPU快，可能因为运行在Rosetta 2下")
            print("   建议安装ARM64原生Python以获得完整GPU加速")
    except Exception as e:
        print(f"MPS测试失败: {e}")
        print("这可能是因为运行在Intel Python下")

print("\n=== 建议 ===\n")

result = subprocess.run(['file', sys.executable], capture_output=True, text=True)
if 'x86_64' in result.stdout:
    print("🔴 当前使用Intel版本Python（Rosetta 2）")
    print("\n推荐操作:")
    print("1. 安装ARM64版本的Miniforge:")
    print("   curl -L -O https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-arm64.sh")
    print("   bash Miniforge3-MacOSX-arm64.sh")
    print("\n2. 或者使用detection_skip参数优化当前环境:")
    print("   在ComfyUI中设置 detection_skip=5 可提升约5倍速度")
else:
    print("✅ 当前使用ARM64原生Python")
    print("   性能已优化，如果还是慢，检查LaMA是否支持MPS")

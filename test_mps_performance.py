#!/usr/bin/env python3
"""
MPS 性能测试 - 更准确的测试方法
"""

import torch
import time
import numpy as np

def test_device_performance(device_name, size=2000, iterations=50):
    """测试指定设备的性能"""
    print(f"\n{'='*60}")
    print(f"测试设备: {device_name}")
    print(f"矩阵大小: {size}x{size}")
    print(f"迭代次数: {iterations}")
    print(f"{'='*60}")

    device = torch.device(device_name)

    # 预热
    print("预热中...")
    a = torch.randn(size, size, device=device)
    b = torch.randn(size, size, device=device)
    for _ in range(5):
        c = torch.matmul(a, b)

    if device_name == 'mps':
        torch.mps.synchronize()

    # 测试矩阵乘法
    print("测试矩阵乘法...")
    times = []
    for i in range(iterations):
        start = time.time()
        c = torch.matmul(a, b)

        if device_name == 'mps':
            torch.mps.synchronize()

        elapsed = time.time() - start
        times.append(elapsed)

    avg_time = np.mean(times)
    std_time = np.std(times)

    print(f"平均时间: {avg_time*1000:.2f} ms")
    print(f"标准差: {std_time*1000:.2f} ms")
    print(f"吞吐量: {1/avg_time:.2f} 次/秒")

    return avg_time

def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║  MPS vs CPU 性能对比测试                                    ║
╚══════════════════════════════════════════════════════════════╝
    """)

    # 检查设备可用性
    print("检查可用设备:")
    print(f"  CPU: ✓")
    print(f"  MPS: {'✓' if torch.backends.mps.is_available() else '✗'}")
    print(f"  CUDA: {'✓' if torch.cuda.is_available() else '✗'}")

    if not torch.backends.mps.is_available():
        print("\n错误: MPS 不可用")
        return

    # 测试不同矩阵大小
    sizes = [1000, 2000, 4000]

    for size in sizes:
        print(f"\n{'#'*60}")
        print(f"# 测试矩阵大小: {size}x{size}")
        print(f"{'#'*60}")

        cpu_time = test_device_performance('cpu', size=size, iterations=20)
        mps_time = test_device_performance('mps', size=size, iterations=20)

        speedup = cpu_time / mps_time

        print(f"\n{'='*60}")
        print(f"结果对比 ({size}x{size}):")
        print(f"  CPU 时间: {cpu_time*1000:.2f} ms")
        print(f"  MPS 时间: {mps_time*1000:.2f} ms")
        print(f"  加速比: {speedup:.2f}x")
        if speedup > 1.2:
            print(f"  评价: ✅ MPS 比 CPU 快 {speedup:.2f} 倍")
        elif speedup < 0.8:
            print(f"  评价: ⚠️ MPS 比 CPU 慢 {1/speedup:.2f} 倍")
        else:
            print(f"  评价: ➖ MPS 和 CPU 性能接近")
        print(f"{'='*60}")

if __name__ == "__main__":
    main()

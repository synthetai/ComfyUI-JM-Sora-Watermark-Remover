#!/usr/bin/env python3
"""检查节点实际使用的设备"""
import torch

# 模拟节点的设备选择逻辑
if torch.cuda.is_available():
    device = "cuda"
elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
    device = "mps"
else:
    device = "cpu"

print(f"Florence-2会使用的设备: {device}")

# LaMA的设备选择
lama_device = device if device in ["cuda", "cpu"] else "cpu"
print(f"LaMA会使用的设备: {lama_device}")

if lama_device != device:
    print(f"\n⚠️  性能瓶颈：LaMA在CPU上运行，这是速度慢的主要原因！")
    print(f"   Florence-2使用{device}加速，但LaMA使用{lama_device}（慢70-80%的处理时间）")
else:
    print(f"\n✅ 两个模型都使用{device}加速")

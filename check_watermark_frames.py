#!/usr/bin/env python3
"""
检查视频中哪些帧还有水印残留
用法：python check_watermark_frames.py <原始视频> <处理后视频>
"""
import sys
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
import torch

# 导入节点代码
from nodes import detect_only

def compare_videos(original_path, processed_path, detection_prompt="watermark", max_bbox_percent=10.0, check_every=5):
    """对比原始视频和处理后视频,找出水印残留的帧"""
    print(f"=== 水印残留检查工具 ===")
    print(f"原始视频: {original_path}")
    print(f"处理后视频: {processed_path}")
    print(f"检测提示词: '{detection_prompt}'")
    print(f"每 {check_every} 帧检查一次")
    print()

    # 加载模型
    device = "cuda" if torch.cuda.is_available() else ("mps" if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available() else "cpu")
    print(f"使用设备: {device}")

    from transformers import AutoProcessor, Florence2ForConditionalGeneration
    print("加载Florence-2模型...")
    model = Florence2ForConditionalGeneration.from_pretrained(
        "florence-community/Florence-2-large"
    ).to(device).eval()
    processor = AutoProcessor.from_pretrained("florence-community/Florence-2-large")
    print("✓ 模型加载完成")
    print()

    # 打开视频
    cap_orig = cv2.VideoCapture(str(original_path))
    cap_proc = cv2.VideoCapture(str(processed_path))

    total_frames = int(cap_orig.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap_orig.get(cv2.CAP_PROP_FPS)

    print(f"视频信息: {total_frames} 帧, {fps:.1f} fps")
    print()

    # 检查处理后视频中的水印残留
    print("检查处理后视频的水印残留...")
    print("-" * 60)

    watermark_frames = []
    for frame_idx in range(0, total_frames, check_every):
        cap_proc.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap_proc.read()
        if not ret:
            continue

        pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        bboxes = detect_only(pil_image, model, processor, device, max_bbox_percent, detection_prompt)

        timestamp = frame_idx / fps
        if len(bboxes) > 0:
            watermark_frames.append((frame_idx, timestamp, bboxes))
            print(f"✗ 第{frame_idx:4d}帧 ({timestamp:5.2f}秒): 检测到 {len(bboxes)} 个水印残留")
            for i, bbox in enumerate(bboxes, 1):
                x1, y1, x2, y2 = bbox
                print(f"    水印{i}: ({x1}, {y1}) → ({x2}, {y2})")
        else:
            print(f"✓ 第{frame_idx:4d}帧 ({timestamp:5.2f}秒): 无水印残留")

    cap_orig.release()
    cap_proc.release()

    print()
    print("=" * 60)
    if len(watermark_frames) == 0:
        print("✓✓✓ 所有检查的帧都没有水印残留!处理成功!")
    else:
        print(f"⚠️  发现 {len(watermark_frames)} 个帧还有水印残留:")
        print()
        for frame_idx, timestamp, bboxes in watermark_frames:
            print(f"  第{frame_idx}帧 ({timestamp:.2f}秒): {len(bboxes)} 个水印")

        # 分析时间段
        first_issue = watermark_frames[0]
        last_issue = watermark_frames[-1]
        print()
        print(f"首个问题帧: 第{first_issue[0]}帧 ({first_issue[1]:.2f}秒)")
        print(f"最后问题帧: 第{last_issue[0]}帧 ({last_issue[1]:.2f}秒)")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python check_watermark_frames.py <原始视频> <处理后视频> [detection_prompt] [max_bbox_percent] [check_every]")
        print("示例: python check_watermark_frames.py original.mp4 processed.mp4")
        print("示例: python check_watermark_frames.py original.mp4 processed.mp4 'Sora watermark' 15.0 10")
        sys.exit(1)

    original_path = Path(sys.argv[1])
    processed_path = Path(sys.argv[2])
    detection_prompt = sys.argv[3] if len(sys.argv) > 3 else "watermark"
    max_bbox_percent = float(sys.argv[4]) if len(sys.argv) > 4 else 10.0
    check_every = int(sys.argv[5]) if len(sys.argv) > 5 else 5

    compare_videos(original_path, processed_path, detection_prompt, max_bbox_percent, check_every)

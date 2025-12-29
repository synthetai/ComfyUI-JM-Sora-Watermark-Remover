#!/usr/bin/env python3
"""
模拟ComfyUI视频处理流程的诊断工具
用法：python simulate_processing.py <视频路径>
"""
import sys
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
import torch

# 导入节点代码
from nodes import detect_only, detect_with_enhanced_sensitivity

def simulate_video_processing(video_path, detection_prompt="watermark", max_bbox_percent=15.0,
                              fps=30.0, detection_skip=1, fade_in=1.0, fade_out=1.0,
                              enhanced_detection=True, sample_every=5):
    """
    模拟SoraVideoWatermarkRemover的两遍处理流程
    """
    print(f"=== 模拟ComfyUI视频处理流程 ===")
    print(f"视频: {video_path}")
    print(f"参数:")
    print(f"  detection_prompt: {detection_prompt}")
    print(f"  max_bbox_percent: {max_bbox_percent}")
    print(f"  fps: {fps}")
    print(f"  detection_skip: {detection_skip}")
    print(f"  fade_in: {fade_in}s")
    print(f"  fade_out: {fade_out}s")
    print(f"  enhanced_detection: {enhanced_detection}")
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
    cap = cv2.VideoCapture(str(video_path))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_fps = cap.get(cv2.CAP_PROP_FPS)

    print(f"视频信息: {total_frames} 帧, {video_fps:.1f} fps")
    print()

    # 转换时间到帧数
    fade_in_frames = int(fade_in * fps)
    fade_out_frames = int(fade_out * fps)

    print(f"时间转换: fade_in={fade_in_frames}帧, fade_out={fade_out_frames}帧")
    print()

    # ========== PASS 1: DETECTION (稀疏) ==========
    print("=" * 60)
    print("PASS 1: 稀疏检测 (模拟ComfyUI检测流程)")
    print("=" * 60)

    detections = {}  # frame_idx -> [bbox, bbox, ...]
    detection_frames = list(range(0, total_frames, detection_skip))

    print(f"将检测 {len(detection_frames)} 个帧 (每 {detection_skip} 帧)")
    print()

    # 只采样部分帧来测试
    sample_detection_frames = [f for f in detection_frames if f % sample_every == 0 or f < 100]

    for frame_idx in sample_detection_frames:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            continue

        pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        # 使用与ComfyUI相同的检测逻辑
        if enhanced_detection:
            bboxes = detect_with_enhanced_sensitivity(
                pil_image, model, processor, device,
                max_bbox_percent, detection_prompt
            )
        else:
            bboxes = detect_only(
                pil_image, model, processor, device,
                max_bbox_percent, detection_prompt
            )

        if bboxes:
            detections[frame_idx] = bboxes
            timestamp = frame_idx / fps
            print(f"✓ 第{frame_idx:4d}帧 ({timestamp:5.2f}秒): 检测到 {len(bboxes)} 个水印")
            for i, bbox in enumerate(bboxes, 1):
                x1, y1, x2, y2 = bbox
                print(f"    水印{i}: ({x1:4d}, {y1:4d}) → ({x2:4d}, {y2:4d})")
        else:
            timestamp = frame_idx / fps
            print(f"✗ 第{frame_idx:4d}帧 ({timestamp:5.2f}秒): 未检测到水印")

    cap.release()

    print()
    print(f"检测完成: 在 {len(detections)} 个检测点找到水印")
    print()

    # ========== 时间线扩展 ==========
    print("=" * 60)
    print("时间线扩展 (模拟ComfyUI扩展逻辑)")
    print("=" * 60)

    frame_masks = {}  # frame_idx -> [bbox, ...]

    for det_frame, bboxes in detections.items():
        # 这是ComfyUI中的扩展逻辑
        start_frame = max(0, det_frame - fade_in_frames)
        end_frame = min(total_frames, det_frame + detection_skip + fade_out_frames)

        print(f"检测点 {det_frame}: 扩展到 [{start_frame}, {end_frame}) 共 {end_frame - start_frame} 帧")

        for f in range(start_frame, end_frame):
            if f not in frame_masks:
                frame_masks[f] = []
            for bbox in bboxes:
                if bbox not in frame_masks[f]:
                    frame_masks[f].append(bbox)

    print()
    print(f"扩展完成: {len(frame_masks)} 帧将被修复")
    print()

    # ========== 分析覆盖情况 ==========
    print("=" * 60)
    print("覆盖分析")
    print("=" * 60)

    # 检查前100帧的覆盖情况
    print("前100帧的修复覆盖:")
    uncovered_frames = []

    for frame_idx in range(min(100, total_frames)):
        timestamp = frame_idx / fps
        if frame_idx in frame_masks:
            num_bboxes = len(frame_masks[frame_idx])
            # 显示bbox位置
            bbox_info = ""
            if frame_masks[frame_idx]:
                first_bbox = frame_masks[frame_idx][0]
                x1, y1, x2, y2 = first_bbox
                bbox_info = f" bbox: ({x1:4d}, {y1:4d}) → ({x2:4d}, {y2:4d})"
            print(f"  ✓ 第{frame_idx:3d}帧 ({timestamp:5.2f}秒): 将修复 {num_bboxes} 个区域{bbox_info}")
        else:
            print(f"  ✗ 第{frame_idx:3d}帧 ({timestamp:5.2f}秒): **不会被修复** ⚠️")
            uncovered_frames.append(frame_idx)

    print()

    if uncovered_frames:
        print(f"⚠️  警告: 前100帧中有 {len(uncovered_frames)} 帧不会被修复!")
        print(f"未覆盖的帧: {uncovered_frames[:20]}{'...' if len(uncovered_frames) > 20 else ''}")
        print()
        print("可能的原因:")
        print("1. 这些帧的检测失败了")
        print("2. fade_in/fade_out设置不够大,无法覆盖这些帧")
        print()
        print("建议:")
        print("- 增大 fade_in 参数")
        print("- 减小 detection_skip 到 1 (如果还没有)")
        print("- 尝试不同的 detection_prompt")
    else:
        print("✓ 前100帧全部会被修复")

    print()
    print("=" * 60)
    print("诊断完成")
    print("=" * 60)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python simulate_processing.py <视频路径> [detection_prompt] [max_bbox_percent]")
        print("示例: python simulate_processing.py video.mp4")
        print("示例: python simulate_processing.py video.mp4 'Sora watermark' 15.0")
        sys.exit(1)

    video_path = Path(sys.argv[1])
    detection_prompt = sys.argv[2] if len(sys.argv) > 2 else "watermark"
    max_bbox_percent = float(sys.argv[3]) if len(sys.argv) > 3 else 15.0

    # 使用用户的ComfyUI参数
    simulate_video_processing(
        video_path,
        detection_prompt=detection_prompt,
        max_bbox_percent=max_bbox_percent,
        fps=30.0,
        detection_skip=1,
        fade_in=1.0,
        fade_out=1.0,
        enhanced_detection=True,
        sample_every=5  # 只采样部分帧以节省时间
    )

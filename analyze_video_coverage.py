#!/usr/bin/env python3
"""
视频水印检测覆盖率分析工具

用法：
    python analyze_video_coverage.py video.mp4 [detection_skip] [fade_in] [fade_out]

功能：
    - 分析整个视频的水印检测情况
    - 生成时间轴可视化图
    - 找出没有被检测覆盖的时间段
    - 推荐最佳参数设置
"""

import sys
import cv2
import numpy as np
from pathlib import Path
from PIL import Image
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

def analyze_video_coverage(video_path, detection_skip=1, fade_in_sec=0.0, fade_out_sec=0.0):
    """分析视频的水印检测覆盖率"""

    # 导入模型
    sys.path.insert(0, str(Path(__file__).parent))
    from nodes import detect_only

    print("\n" + "="*70)
    print("  视频水印检测覆盖率分析")
    print("="*70)

    # 加载视频
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"\n视频信息：")
    print(f"  文件: {video_path}")
    print(f"  总帧数: {total_frames}")
    print(f"  帧率: {fps:.2f} fps")
    print(f"  时长: {total_frames/fps:.2f} 秒")

    # 参数设置
    fade_in_frames = int(fade_in_sec * fps)
    fade_out_frames = int(fade_out_sec * fps)

    print(f"\n检测参数：")
    print(f"  detection_skip: {detection_skip} (每{detection_skip}帧检测一次)")
    print(f"  fade_in: {fade_in_sec}秒 ({fade_in_frames}帧)")
    print(f"  fade_out: {fade_out_sec}秒 ({fade_out_frames}帧)")

    # 加载模型
    print(f"\n加载 Florence-2 模型...")
    import torch
    from transformers import AutoProcessor, Florence2ForConditionalGeneration

    device = "mps" if torch.backends.mps.is_available() else "cpu"

    model = Florence2ForConditionalGeneration.from_pretrained(
        "florence-community/Florence-2-large"
    ).to(device).eval()

    processor = AutoProcessor.from_pretrained(
        "florence-community/Florence-2-large"
    )

    print(f"✓ 模型已加载到 {device}")

    # Pass 1: 稀疏检测
    print(f"\n{'='*70}")
    print("Pass 1: 稀疏检测")
    print(f"{'='*70}")

    detections = {}  # frame_idx -> has_watermark
    detection_frames = list(range(0, total_frames, detection_skip))

    print(f"将检测 {len(detection_frames)} 个采样点...")

    for i, frame_idx in enumerate(detection_frames):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            break

        # 转换为 PIL
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(frame_rgb)

        # 检测
        bboxes = detect_only(
            pil_image, model, processor, device,
            max_bbox_percent=10.0,
            detection_prompt="watermark"
        )

        detections[frame_idx] = len(bboxes) > 0

        if (i + 1) % 10 == 0 or (i + 1) == len(detection_frames):
            print(f"  进度: {i+1}/{len(detection_frames)} ({(i+1)/len(detection_frames)*100:.1f}%)")

    cap.release()

    # 统计检测结果
    detected_count = sum(1 for v in detections.values() if v)
    print(f"\n检测统计：")
    print(f"  检测点总数: {len(detections)}")
    print(f"  发现水印: {detected_count} 个点")
    print(f"  检测率: {detected_count/len(detections)*100:.1f}%")

    # Pass 2: 时间扩展
    print(f"\n{'='*70}")
    print("Pass 2: 时间扩展模拟")
    print(f"{'='*70}")

    # 模拟时间扩展后哪些帧会被处理
    covered_frames = set()

    for frame_idx, has_watermark in detections.items():
        if has_watermark:
            # 扩展时间范围
            start = max(0, frame_idx - fade_in_frames)
            end = min(total_frames - 1, frame_idx + fade_out_frames)
            for f in range(start, end + 1):
                covered_frames.add(f)

    print(f"\n扩展后覆盖范围：")
    print(f"  覆盖帧数: {len(covered_frames)}/{total_frames}")
    print(f"  覆盖率: {len(covered_frames)/total_frames*100:.1f}%")
    print(f"  未覆盖: {total_frames - len(covered_frames)} 帧")

    # 找出未覆盖的时间段
    uncovered = sorted(set(range(total_frames)) - covered_frames)

    if uncovered:
        print(f"\n⚠️  发现 {len(uncovered)} 帧未被覆盖！")
        print(f"\n未覆盖的时间段：")

        # 合并连续的帧为时间段
        segments = []
        if uncovered:
            start = uncovered[0]
            prev = uncovered[0]

            for frame in uncovered[1:]:
                if frame != prev + 1:
                    # 新段落
                    segments.append((start, prev))
                    start = frame
                prev = frame

            segments.append((start, prev))

        for i, (start, end) in enumerate(segments[:10], 1):  # 只显示前10个
            start_time = start / fps
            end_time = end / fps
            duration = end_time - start_time
            print(f"  {i}. 帧 {start}-{end} ({start_time:.2f}s - {end_time:.2f}s, 持续 {duration:.2f}s)")

        if len(segments) > 10:
            print(f"  ... 还有 {len(segments)-10} 个时间段未显示")
    else:
        print(f"\n✓ 所有帧都已覆盖！")

    # 生成可视化
    print(f"\n{'='*70}")
    print("生成时间轴可视化...")
    print(f"{'='*70}")

    fig, ax = plt.subplots(figsize=(16, 6))

    # 绘制所有帧（灰色背景）
    ax.barh(0, total_frames, height=0.5, color='lightgray', label='未检测帧')

    # 绘制检测点（红点）
    detection_x = list(detections.keys())
    detection_y = [0] * len(detection_x)
    detection_colors = ['red' if detections[x] else 'gray' for x in detection_x]
    ax.scatter(detection_x, detection_y, c=detection_colors, s=100, zorder=3,
               label='检测点 (红=发现水印)', marker='|')

    # 绘制覆盖范围（绿色）
    if covered_frames:
        # 合并连续帧
        covered_sorted = sorted(covered_frames)
        start = covered_sorted[0]
        prev = covered_sorted[0]

        for frame in covered_sorted[1:] + [covered_sorted[-1] + 2]:
            if frame != prev + 1:
                # 绘制这一段
                ax.barh(0, prev - start + 1, left=start, height=0.5,
                       color='green', alpha=0.6, zorder=2)
                start = frame
            prev = frame

    ax.set_ylim(-0.5, 0.5)
    ax.set_xlim(0, total_frames)
    ax.set_xlabel(f'帧数 (总计 {total_frames} 帧, {total_frames/fps:.1f}秒 @ {fps:.1f}fps)', fontsize=12)
    ax.set_yticks([])
    ax.set_title(f'水印检测覆盖率分析 - 覆盖: {len(covered_frames)/total_frames*100:.1f}%',
                fontsize=14, fontweight='bold')

    # 添加图例
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='lightgray', label='未覆盖帧'),
        Patch(facecolor='green', alpha=0.6, label='已覆盖帧'),
        plt.Line2D([0], [0], marker='|', color='w', markerfacecolor='red',
                   markersize=10, label='检测到水印'),
        plt.Line2D([0], [0], marker='|', color='w', markerfacecolor='gray',
                   markersize=10, label='未检测到水印'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=10)

    # 添加网格
    ax.grid(True, alpha=0.3, axis='x')

    plt.tight_layout()

    output_file = Path(video_path).stem + "_coverage.png"
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✓ 时间轴图已保存: {output_file}")

    # 推荐参数
    print(f"\n{'='*70}")
    print("参数优化建议")
    print(f"{'='*70}")

    coverage_rate = len(covered_frames) / total_frames

    if coverage_rate < 0.95:
        print(f"\n⚠️  当前覆盖率 {coverage_rate*100:.1f}% 偏低，建议优化：")
        print(f"\n方案1: 降低 detection_skip（提高检测密度）")
        print(f"  当前: detection_skip = {detection_skip}")
        print(f"  建议: detection_skip = 1  # 每帧都检测，100%覆盖")

        print(f"\n方案2: 增加时间扩展范围")
        print(f"  当前: fade_in={fade_in_sec}s, fade_out={fade_out_sec}s")

        # 计算需要的扩展范围
        max_gap = 0
        if len(uncovered) > 1:
            gaps = [uncovered[i+1] - uncovered[i] for i in range(len(uncovered)-1)]
            max_gap = max(gaps) if gaps else 0

        suggested_extend = max(1.0, max_gap / fps * 1.5)
        print(f"  建议: fade_in={suggested_extend:.1f}s, fade_out={suggested_extend:.1f}s")

        print(f"\n方案3: 降低 max_bbox_percent（提高检测灵敏度）")
        print(f"  当前: max_bbox_percent = 10.0")
        print(f"  建议: max_bbox_percent = 15.0  # 检测更大范围的水印")
    else:
        print(f"\n✓ 当前参数设置良好，覆盖率 {coverage_rate*100:.1f}%")
        print(f"\n如果仍有残留水印，可能是：")
        print(f"  1. LaMA 修复质量问题 → 使用 quality_mode='high'")
        print(f"  2. 检测框不够精确 → 调整 max_bbox_percent")
        print(f"  3. 某些帧水印太透明 → 降低 max_bbox_percent")

    print(f"\n{'='*70}")
    print(f"分析完成！")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python analyze_video_coverage.py <video_file> [detection_skip] [fade_in] [fade_out]")
        print("\n示例:")
        print("  python analyze_video_coverage.py video.mp4")
        print("  python analyze_video_coverage.py video.mp4 3 0.5 0.5")
        sys.exit(1)

    video_path = sys.argv[1]
    detection_skip = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    fade_in = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
    fade_out = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0

    analyze_video_coverage(video_path, detection_skip, fade_in, fade_out)

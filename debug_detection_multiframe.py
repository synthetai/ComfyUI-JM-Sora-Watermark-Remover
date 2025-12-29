#!/usr/bin/env python3
"""
诊断工具：测试视频多个关键帧的水印检测
用法：python debug_detection_multiframe.py <视频路径>
"""
import sys
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw
import torch

# 导入节点代码
from nodes import detect_only

def test_multi_frame_detection(file_path, detection_prompt="watermark", max_bbox_percent=10.0):
    """测试视频多个关键帧的水印检测"""
    print(f"=== 多帧水印检测诊断工具 ===")
    print(f"文件: {file_path}")
    print(f"检测提示词: '{detection_prompt}'")
    print(f"最大bbox百分比: {max_bbox_percent}%")
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

    # 加载视频
    file_path = Path(file_path)
    if file_path.suffix.lower() not in ['.mp4', '.avi', '.mov', '.mkv']:
        print(f"❌ 请提供视频文件")
        return

    cap = cv2.VideoCapture(str(file_path))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"视频信息: {total_frames} 帧, {fps:.1f} fps, 时长 {total_frames/fps:.1f} 秒")
    print()

    # 测试关键帧: 第0帧, 第30帧(1秒), 第60帧(2秒), 中间帧
    test_frames = [
        (0, "开始"),
        (int(fps * 0.5) if fps > 0 else 15, "0.5秒"),
        (int(fps * 1.0) if fps > 0 else 30, "1.0秒"),
        (int(fps * 2.0) if fps > 0 else 60, "2.0秒"),
        (total_frames // 2, "中间")
    ]

    # 过滤超出范围的帧
    test_frames = [(f, label) for f, label in test_frames if f < total_frames]

    print(f"将测试 {len(test_frames)} 个关键帧:")
    for frame_idx, label in test_frames:
        print(f"  - 第{frame_idx}帧 ({label})")
    print()

    # 检测每一帧
    results = {}
    for frame_idx, label in test_frames:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            print(f"⚠️  无法读取第{frame_idx}帧")
            continue

        pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        # 运行检测
        bboxes = detect_only(pil_image, model, processor, device, max_bbox_percent, detection_prompt)
        results[frame_idx] = (label, bboxes, pil_image)

        if len(bboxes) > 0:
            print(f"✓ 第{frame_idx}帧 ({label}): 检测到 {len(bboxes)} 个水印")
            image_area = pil_image.width * pil_image.height
            for i, bbox in enumerate(bboxes, 1):
                x1, y1, x2, y2 = bbox
                area = (x2 - x1) * (y2 - y1)
                area_percent = (area / image_area) * 100
                print(f"    水印{i}: ({x1}, {y1}) → ({x2}, {y2}), 大小 {x2-x1}x{y2-y1}, 占比 {area_percent:.2f}%")
        else:
            print(f"✗ 第{frame_idx}帧 ({label}): 未检测到水印")

    cap.release()
    print()

    # 分析结果
    detected_frames = [f for f, (_, bboxes, _) in results.items() if len(bboxes) > 0]
    if len(detected_frames) == 0:
        print("=== ❌ 所有测试帧都未检测到水印 ===")
        print()
        print("建议:")
        print("1. 尝试不同的 detection_prompt:")
        print("   python debug_detection_multiframe.py video.mp4 'Sora watermark'")
        print("   python debug_detection_multiframe.py video.mp4 'logo'")
        print("2. 增大 max_bbox_percent:")
        print("   python debug_detection_multiframe.py video.mp4 watermark 20.0")
        return

    # 保存标注图片
    print("=== 检测结果分析 ===")
    first_detected = min(detected_frames)
    last_detected = max(detected_frames)

    print(f"首次检测到水印: 第{first_detected}帧 ({results[first_detected][0]})")
    print(f"最后检测到水印: 第{last_detected}帧 ({results[last_detected][0]})")
    print()

    if 0 not in detected_frames and len(detected_frames) > 0:
        print("⚠️  **关键发现**: 第0帧(视频开始)没有检测到水印!")
        print(f"   但在第{first_detected}帧({results[first_detected][0]})检测到了水印")
        print()
        print("这解释了为什么视频前1秒的水印没有被去掉。")
        print()
        print("解决方案:")
        print(f"1. 在ComfyUI节点中设置 fade_in={first_detected/fps:.1f} 秒或更大")
        print(f"   这样会从第{first_detected}帧向前扩展到第0帧")
        print("2. 设置 detection_skip=1 确保每一帧都被检测")
        print("3. 尝试不同的 detection_prompt 提高第0帧的检测成功率")

    # 保存标注图片
    print()
    for frame_idx, (label, bboxes, pil_image) in results.items():
        if len(bboxes) > 0:
            draw = ImageDraw.Draw(pil_image)
            for bbox in bboxes:
                x1, y1, x2, y2 = bbox
                draw.rectangle([x1, y1, x2, y2], outline=(0, 255, 0), width=3)

            output_path = file_path.parent / f"{file_path.stem}_frame{frame_idx}_{label}_detected.png"
            pil_image.save(output_path)
            print(f"✓ 已保存标注图片: {output_path.name}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python debug_detection_multiframe.py <视频路径> [detection_prompt] [max_bbox_percent]")
        print("示例: python debug_detection_multiframe.py video.mp4")
        print("示例: python debug_detection_multiframe.py video.mp4 'Sora watermark' 15.0")
        sys.exit(1)

    file_path = sys.argv[1]
    detection_prompt = sys.argv[2] if len(sys.argv) > 2 else "watermark"
    max_bbox_percent = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0

    test_multi_frame_detection(file_path, detection_prompt, max_bbox_percent)

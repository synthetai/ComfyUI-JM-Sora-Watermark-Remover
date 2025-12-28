#!/usr/bin/env python3
"""
诊断工具：测试水印检测是否正常工作
用法：python debug_detection.py <视频或图片路径>
"""
import sys
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw
import torch

# 导入节点代码
from nodes import detect_only

def test_detection(file_path, detection_prompt="watermark", max_bbox_percent=10.0):
    """测试单张图片/视频帧的水印检测"""
    print(f"=== 水印检测诊断工具 ===")
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

    # 加载图片
    file_path = Path(file_path)
    if file_path.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv']:
        # 视频文件：提取中间帧
        print("检测到视频文件，提取中间帧...")
        cap = cv2.VideoCapture(str(file_path))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 2)
        ret, frame = cap.read()
        cap.release()
        if not ret:
            print(f"❌ 无法读取视频帧")
            return
        pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        print(f"✓ 提取第 {total_frames // 2}/{total_frames} 帧")
    else:
        # 图片文件
        pil_image = Image.open(file_path).convert("RGB")
        print(f"✓ 图片加载成功")

    print(f"图片尺寸: {pil_image.width} x {pil_image.height}")
    print()

    # 运行检测
    print("开始检测水印...")
    bboxes = detect_only(pil_image, model, processor, device, max_bbox_percent, detection_prompt)

    print(f"检测结果: 找到 {len(bboxes)} 个水印区域")
    print()

    if len(bboxes) == 0:
        print("⚠️  未检测到水印！")
        print()
        print("可能的原因:")
        print("1. detection_prompt 不匹配水印内容")
        print("   - 尝试: 'Sora watermark', 'Sora logo', 'watermark', 'logo'")
        print("2. max_bbox_percent 设置太小，过滤掉了检测结果")
        print("   - 尝试增大到 15.0 或 20.0")
        print("3. 图片中确实没有水印")
        print()
        print("建议: 尝试不同的 detection_prompt 参数")
        return

    # 显示检测详情
    image_area = pil_image.width * pil_image.height
    for i, bbox in enumerate(bboxes, 1):
        x1, y1, x2, y2 = bbox
        area = (x2 - x1) * (y2 - y1)
        area_percent = (area / image_area) * 100
        print(f"水印 {i}:")
        print(f"  位置: x1={x1}, y1={y1}, x2={x2}, y2={y2}")
        print(f"  大小: {x2-x1} x {y2-y1} 像素")
        print(f"  占比: {area_percent:.2f}%")
        print()

    # 保存带标注的图片
    draw = ImageDraw.Draw(pil_image)
    for bbox in bboxes:
        x1, y1, x2, y2 = bbox
        draw.rectangle([x1, y1, x2, y2], outline=(0, 255, 0), width=3)

    output_path = file_path.parent / f"{file_path.stem}_detected.png"
    pil_image.save(output_path)
    print(f"✓ 已保存标注图片到: {output_path}")
    print()
    print("=== 检测成功 ===")
    print("如果标注的区域正确，说明检测正常工作。")
    print("如果ComfyUI中还是没有移除水印，可能是LaMA修复的问题。")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python debug_detection.py <图片或视频路径> [detection_prompt] [max_bbox_percent]")
        print("示例: python debug_detection.py video.mp4")
        print("示例: python debug_detection.py image.jpg 'Sora watermark' 15.0")
        sys.exit(1)

    file_path = sys.argv[1]
    detection_prompt = sys.argv[2] if len(sys.argv) > 2 else "watermark"
    max_bbox_percent = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0

    test_detection(file_path, detection_prompt, max_bbox_percent)

#!/usr/bin/env python3
"""
测试水印检测精度 - 生成不同参数的对比图
"""
import sys
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def test_detection_precision(video_path, output_dir="detection_tests"):
    """测试不同参数的检测效果"""
    from nodes import load_florence2_model, detect_watermark_bboxes_only
    
    # 创建输出目录
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # 加载视频第一帧
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("❌ 无法读取视频")
        return
    
    # 转换为 PIL Image
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(frame_rgb)
    
    # 加载模型
    print("加载 Florence-2 模型...")
    import torch
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model, processor = load_florence2_model(device)
    
    # 测试不同的参数组合
    test_configs = [
        {"prompt": "watermark", "max_percent": 10.0, "name": "default"},
        {"prompt": "watermark", "max_percent": 5.0, "name": "stricter_5pct"},
        {"prompt": "watermark", "max_percent": 3.0, "name": "stricter_3pct"},
        {"prompt": "Sora watermark", "max_percent": 10.0, "name": "sora_prompt"},
        {"prompt": "Sora watermark", "max_percent": 5.0, "name": "sora_5pct"},
        {"prompt": "logo", "max_percent": 10.0, "name": "logo_prompt"},
    ]
    
    print(f"\n测试 {len(test_configs)} 种配置...\n")
    
    for config in test_configs:
        prompt = config["prompt"]
        max_pct = config["max_percent"]
        name = config["name"]
        
        print(f"测试: {name}")
        print(f"  - prompt: '{prompt}'")
        print(f"  - max_bbox_percent: {max_pct}%")
        
        # 检测
        bboxes = detect_watermark_bboxes_only(
            image, model, processor, device, prompt, max_pct
        )
        
        # 绘制结果
        img_with_boxes = frame_rgb.copy()
        
        if bboxes:
            print(f"  ✓ 检测到 {len(bboxes)} 个水印")
            for i, bbox in enumerate(bboxes):
                x1, y1, x2, y2 = bbox
                width = x2 - x1
                height = y2 - y1
                area_pct = (width * height) / (image.width * image.height) * 100
                
                print(f"    水印 {i+1}: ({x1},{y1}) -> ({x2},{y2})")
                print(f"             尺寸: {width}x{height} px ({area_pct:.2f}%)")
                
                # 绘制红框
                cv2.rectangle(img_with_boxes, (x1, y1), (x2, y2), (255, 0, 0), 3)
                
                # 标注尺寸信息
                label = f"{width}x{height} ({area_pct:.1f}%)"
                cv2.putText(img_with_boxes, label, (x1, y1-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        else:
            print(f"  ✗ 未检测到水印")
        
        # 保存
        output_file = output_path / f"{name}.png"
        cv2.imwrite(str(output_file), cv2.cvtColor(img_with_boxes, cv2.COLOR_RGB2BGR))
        print(f"  已保存: {output_file}\n")
    
    print(f"\n{'='*60}")
    print(f"所有测试完成！对比图片保存在: {output_path}/")
    print(f"{'='*60}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python test_detection_precision.py <video_file>")
        sys.exit(1)
    
    test_detection_precision(sys.argv[1])

#!/usr/bin/env python3
"""
ComfyUI-JM-Sora-Watermark-Remover 综合诊断工具

用法：
    python diagnose.py

功能：
    - 检测Python环境和架构
    - 检测所有依赖版本
    - 验证模型是否可用
    - 检测GPU/MPS加速
    - 提供针对性的修复建议
"""

import sys
import platform
import subprocess
from pathlib import Path

def print_header(title):
    """打印章节标题"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")

def print_ok(message):
    """打印成功消息"""
    print(f"✅ {message}")

def print_warning(message):
    """打印警告消息"""
    print(f"⚠️  {message}")

def print_error(message):
    """打印错误消息"""
    print(f"❌ {message}")

def check_system():
    """检查系统信息"""
    print_header("系统信息")

    system = platform.system()
    machine = platform.machine()
    python_version = sys.version.split()[0]

    print(f"操作系统: {system}")
    print(f"CPU架构: {machine}")
    print(f"Python版本: {python_version}")
    print(f"Python路径: {sys.executable}")

    # 检查Python架构
    result = subprocess.run(['file', sys.executable], capture_output=True, text=True)

    issues = []

    if system == "Darwin":  # macOS
        if 'x86_64' in result.stdout and machine == 'arm64':
            print_error("Python架构: Intel x86_64 (Rosetta 2)")
            print("   系统是ARM64 (M1/M2/M3) 但Python是Intel版本")
            print("   性能损失: 约30-50%")
            issues.append({
                'type': 'architecture',
                'severity': 'high',
                'message': 'Python运行在Rosetta 2下',
                'fix': 'install_arm64_python'
            })
        elif 'arm64' in result.stdout:
            print_ok("Python架构: ARM64 (原生)")
        else:
            print_warning(f"未知架构: {result.stdout}")
    elif system == "Linux":
        print_ok(f"Python架构: {machine}")

    return issues

def check_dependencies():
    """检查Python依赖"""
    print_header("依赖版本检查")

    issues = []

    # 必需的包和最低版本
    required = {
        'torch': '2.0.0',
        'transformers': '4.38.1',  # 注意不是4.38.0
        'timm': '0.9.0',
        'einops': '0.7.0',
        'opencv-python': '4.8.0',
        'PIL': '10.0.0',
        'loguru': None,
        'iopaint': None,
    }

    for package, min_version in required.items():
        package_name = package
        if package == 'PIL':
            package_name = 'Pillow'
        elif package == 'opencv-python':
            package_name = 'cv2'

        try:
            if package_name == 'cv2':
                import cv2
                version = cv2.__version__
            elif package_name == 'Pillow':
                from PIL import Image
                import PIL
                version = PIL.__version__
            else:
                mod = __import__(package_name)
                version = mod.__version__

            # 版本比较
            if min_version:
                from packaging import version as pkg_version
                if pkg_version.parse(version) >= pkg_version.parse(min_version):
                    print_ok(f"{package}: {version} (>= {min_version})")
                else:
                    print_error(f"{package}: {version} (需要 >= {min_version})")
                    issues.append({
                        'type': 'dependency',
                        'severity': 'critical',
                        'package': package,
                        'current': version,
                        'required': min_version,
                        'fix': 'upgrade_package'
                    })
            else:
                print_ok(f"{package}: {version}")

        except ImportError:
            print_error(f"{package}: 未安装")
            issues.append({
                'type': 'dependency',
                'severity': 'critical',
                'package': package,
                'current': None,
                'required': min_version,
                'fix': 'install_package'
            })

    # 特别检查transformers是否为4.38.0
    try:
        import transformers
        if transformers.__version__ == '4.38.0':
            print_error("transformers: 4.38.0 (此版本不包含Florence2!)")
            print("   必须升级到 4.38.1 或更高版本")
            issues.append({
                'type': 'dependency',
                'severity': 'critical',
                'package': 'transformers',
                'current': '4.38.0',
                'required': '4.38.1',
                'fix': 'upgrade_transformers_438'
            })
    except:
        pass

    return issues

def check_florence2():
    """检查Florence-2是否可导入"""
    print_header("Florence-2 模型检查")

    issues = []

    try:
        from transformers import Florence2ForConditionalGeneration, AutoProcessor
        print_ok("Florence2ForConditionalGeneration 可以导入")
        print_ok("AutoProcessor 可以导入")
    except ImportError as e:
        print_error(f"无法导入Florence-2: {e}")
        issues.append({
            'type': 'model',
            'severity': 'critical',
            'message': 'Florence-2无法导入',
            'fix': 'upgrade_transformers'
        })

    return issues

def check_lama():
    """检查LaMA模型"""
    print_header("LaMA 模型检查")

    issues = []

    # 检查模型文件
    lama_path = Path.home() / ".cache" / "torch" / "hub" / "checkpoints" / "big-lama.pt"

    if lama_path.exists():
        size_mb = lama_path.stat().st_size / (1024 * 1024)
        if size_mb > 190 and size_mb < 200:
            print_ok(f"LaMA模型文件存在: {lama_path}")
            print(f"   文件大小: {size_mb:.1f} MB")
        else:
            print_warning(f"LaMA模型文件大小异常: {size_mb:.1f} MB (应该约196MB)")
            issues.append({
                'type': 'model',
                'severity': 'medium',
                'message': 'LaMA模型文件可能损坏',
                'fix': 'redownload_lama'
            })
    else:
        print_error(f"LaMA模型文件不存在: {lama_path}")
        issues.append({
            'type': 'model',
            'severity': 'critical',
            'message': 'LaMA模型未下载',
            'fix': 'download_lama'
        })

    # 检查IOPaint
    try:
        from iopaint.model_manager import ModelManager
        print_ok("IOPaint 可以导入")
    except ImportError as e:
        print_error(f"IOPaint 无法导入: {e}")
        issues.append({
            'type': 'dependency',
            'severity': 'critical',
            'package': 'iopaint',
            'fix': 'install_iopaint'
        })

    return issues

def check_gpu():
    """检查GPU加速"""
    print_header("GPU 加速检查")

    issues = []

    try:
        import torch

        # CUDA
        if torch.cuda.is_available():
            print_ok(f"CUDA 可用")
            print(f"   CUDA版本: {torch.version.cuda}")
            print(f"   GPU数量: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                print(f"   GPU {i}: {torch.cuda.get_device_name(i)}")
        else:
            print_warning("CUDA 不可用")

        # MPS (Apple Silicon)
        if hasattr(torch.backends, 'mps'):
            if torch.backends.mps.is_available():
                print_ok("MPS (Apple GPU) 可用")

                # 性能测试
                try:
                    import time
                    size = 1000
                    cpu_tensor = torch.randn(size, size)
                    mps_tensor = cpu_tensor.to('mps')

                    start = time.time()
                    for _ in range(10):
                        _ = torch.matmul(cpu_tensor, cpu_tensor)
                    cpu_time = time.time() - start

                    start = time.time()
                    for _ in range(10):
                        _ = torch.matmul(mps_tensor, mps_tensor)
                    torch.mps.synchronize()
                    mps_time = time.time() - start

                    speedup = cpu_time / mps_time

                    if speedup > 1.2:
                        print_ok(f"   MPS性能测试: {speedup:.2f}x 加速")
                    elif speedup < 0.8:
                        print_warning(f"   MPS性能测试: {speedup:.2f}x (比CPU慢!)")
                        print("   这通常表示Python运行在Rosetta 2下")
                        issues.append({
                            'type': 'performance',
                            'severity': 'high',
                            'message': 'MPS性能异常',
                            'fix': 'check_architecture'
                        })
                    else:
                        print_warning(f"   MPS性能测试: {speedup:.2f}x (性能一般)")

                except Exception as e:
                    print_warning(f"   MPS性能测试失败: {e}")
            else:
                print_warning("MPS 不可用")

        # 设备选择
        if torch.cuda.is_available():
            device = "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"

        print(f"\n当前会使用的设备: {device}")

        if device == "cpu":
            print_warning("将使用CPU处理，速度会很慢")
            print("建议：")
            if platform.system() == "Darwin":
                print("  - 确保安装了支持MPS的PyTorch版本")
                print("  - 使用ARM64原生Python以获得更好的MPS支持")
            else:
                print("  - 安装CUDA版本的PyTorch以使用GPU加速")

    except ImportError:
        print_error("PyTorch 未安装")
        issues.append({
            'type': 'dependency',
            'severity': 'critical',
            'package': 'torch',
            'fix': 'install_pytorch'
        })

    return issues

def generate_fix_commands(issues):
    """生成修复命令"""
    if not issues:
        print_header("诊断结果")
        print_ok("所有检查通过！环境配置正确。")
        return

    print_header("发现的问题")

    critical = [i for i in issues if i.get('severity') == 'critical']
    high = [i for i in issues if i.get('severity') == 'high']
    medium = [i for i in issues if i.get('severity') == 'medium']

    if critical:
        print(f"\n🔴 严重问题 ({len(critical)}个):")
        for issue in critical:
            if issue['type'] == 'dependency':
                pkg = issue.get('package', '未知')
                current = issue.get('current', '未安装')
                required = issue.get('required', '未知')
                print(f"  - {pkg}: {current} (需要 >= {required})")
            else:
                print(f"  - {issue.get('message', '未知问题')}")

    if high:
        print(f"\n⚠️  高优先级问题 ({len(high)}个):")
        for issue in high:
            print(f"  - {issue.get('message', '未知问题')}")

    if medium:
        print(f"\n⚠️  中等问题 ({len(medium)}个):")
        for issue in medium:
            print(f"  - {issue.get('message', '未知问题')}")

    print_header("修复建议")

    # 检查是否是架构问题
    arch_issues = [i for i in issues if i.get('type') == 'architecture']
    if arch_issues:
        print("\n📋 步骤1: 修复Python架构问题 (推荐)")
        print("─" * 60)
        print("当前Python是Intel版本，建议安装ARM64原生版本获得最佳性能。")
        print("\n安装ARM64版本的Miniforge:")
        print("```bash")
        print("curl -L -O https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-arm64.sh")
        print("bash Miniforge3-MacOSX-arm64.sh")
        print("```")
        print("\n或者暂时使用Intel版本，但需要优化参数:")
        print("在ComfyUI中设置 detection_skip=5 来提升速度")

    # 检查依赖问题
    dep_issues = [i for i in issues if i.get('type') == 'dependency']
    if dep_issues:
        step_num = 2 if arch_issues else 1
        print(f"\n📋 步骤{step_num}: 修复依赖问题")
        print("─" * 60)

        # 生成pip命令
        to_upgrade = []
        to_install = []

        for issue in dep_issues:
            pkg = issue.get('package')
            if pkg:
                if issue.get('current'):
                    to_upgrade.append(pkg)
                else:
                    to_install.append(pkg)

        if to_upgrade or to_install:
            print("运行以下命令修复依赖:")
            print("```bash")

            # 特别处理transformers 4.38.0
            if any(i.get('fix') == 'upgrade_transformers_438' for i in dep_issues):
                print("# 升级transformers (4.38.0不包含Florence2，必须升级)")
                print("pip install --upgrade transformers==4.57.3")
                print()

            if 'transformers' in to_upgrade and not any(i.get('fix') == 'upgrade_transformers_438' for i in dep_issues):
                print("# 升级transformers到最新版本")
                print("pip install --upgrade transformers>=4.38.1")
                print()

            other_upgrades = [p for p in to_upgrade if p != 'transformers']
            if other_upgrades:
                print("# 升级其他依赖")
                for pkg in other_upgrades:
                    print(f"pip install --upgrade {pkg}")
                print()

            if to_install:
                print("# 安装缺失的依赖")
                for pkg in to_install:
                    if pkg == 'iopaint':
                        print("pip install iopaint --no-deps")
                    else:
                        print(f"pip install {pkg}")
                print()

            print("# 或一键安装所有依赖")
            print("cd /path/to/ComfyUI-JM-Sora-Watermark-Remover")
            print("python install.py")
            print("```")

    # 检查模型问题
    model_issues = [i for i in issues if i.get('type') == 'model']
    if model_issues:
        step_num = len([arch_issues, dep_issues]) + 1 if (arch_issues or dep_issues) else 1
        print(f"\n📋 步骤{step_num}: 下载模型")
        print("─" * 60)
        print("运行安装脚本下载所需模型:")
        print("```bash")
        print("cd /path/to/ComfyUI-JM-Sora-Watermark-Remover")
        print("python install.py")
        print("```")

    print("\n" + "="*60)
    print("修复完成后，重启ComfyUI并重新运行此诊断脚本验证。")
    print("="*60)

def main():
    """主函数"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║  ComfyUI-JM-Sora-Watermark-Remover 环境诊断工具             ║
║  版本: 1.0                                                   ║
╚══════════════════════════════════════════════════════════════╝
    """)

    all_issues = []

    # 执行所有检查
    all_issues.extend(check_system())
    all_issues.extend(check_dependencies())
    all_issues.extend(check_florence2())
    all_issues.extend(check_lama())
    all_issues.extend(check_gpu())

    # 生成修复建议
    generate_fix_commands(all_issues)

    # 返回状态码
    if any(i.get('severity') == 'critical' for i in all_issues):
        sys.exit(1)
    elif all_issues:
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()

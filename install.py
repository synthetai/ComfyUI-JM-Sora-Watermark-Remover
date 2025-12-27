import subprocess
import sys
import os
from pathlib import Path
import urllib.request

def check_package_version(package_name):
    """Check if package is installed and return version."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", package_name],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.startswith('Version:'):
                    return line.split(':')[1].strip()
        return None
    except:
        return None

def download_file(url, dest_path, desc="File"):
    """Download file with progress."""
    print(f"Downloading {desc}...")
    print(f"URL: {url}")
    print(f"Destination: {dest_path}")

    try:
        urllib.request.urlretrieve(url, dest_path)
        print(f"✓ {desc} downloaded successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to download {desc}: {e}")
        return False

def install():
    """Install dependencies and download required models."""

    print("=" * 60)
    print("Installing ComfyUI-JM-Sora-Watermark-Remover dependencies...")
    print("=" * 60)

    # Get the current directory
    current_dir = Path(__file__).parent
    requirements_file = current_dir / "requirements.txt"

    # Check existing packages to avoid conflicts
    print("\n[1/5] Checking existing packages...")
    peft_version = check_package_version("peft")
    diffusers_version = check_package_version("diffusers")

    print(f"  Current peft version: {peft_version if peft_version else 'Not installed'}")
    print(f"  Current diffusers version: {diffusers_version if diffusers_version else 'Not installed'}")

    if peft_version:
        print("  Note: Using existing peft version from ComfyUI")
    if diffusers_version:
        print("  Note: Using existing diffusers version from ComfyUI")

    # Install requirements (except iopaint)
    if requirements_file.exists():
        print("\n[2/5] Installing Python dependencies...")
        print("  (This will use ComfyUI's existing packages where possible)")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
            ])
            print("✓ Python dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install Python dependencies: {e}")
            return False
    else:
        print(f"✗ requirements.txt not found at {requirements_file}")
        return False

    # Install iopaint separately with --no-deps (same as reference project)
    print("\n[3/5] Installing iopaint (with --no-deps to avoid conflicts)...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "iopaint", "--no-deps"
        ])
        print("✓ iopaint installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install iopaint: {e}")
        print("  You can install manually: pip install iopaint --no-deps")
        return False

    # Download Florence-2 model
    print("\n[4/5] Checking Florence-2 model...")
    print("Note: Florence-2 model will be automatically downloaded from HuggingFace on first use.")
    print("Model: florence-community/Florence-2-large (~1GB)")
    print("Location: ~/.cache/huggingface/hub/")

    # Download LaMA model directly from GitHub (same as reference project)
    print("\n[5/5] Downloading LaMA inpainting model...")
    print("Model size: ~196MB")

    # Set up LaMA model paths (same as reference project)
    lama_dir = Path.home() / ".cache" / "torch" / "hub" / "checkpoints"
    lama_file = lama_dir / "big-lama.pt"

    if lama_file.exists():
        print(f"✓ LaMA model already exists at {lama_file}")
    else:
        lama_dir.mkdir(parents=True, exist_ok=True)
        lama_url = "https://github.com/Sanster/models/releases/download/add_big_lama/big-lama.pt"

        if not download_file(lama_url, lama_file, "LaMA model"):
            print("\nYou can download it manually later:")
            print(f"  mkdir -p {lama_dir}")
            print(f"  curl -L -o {lama_file} {lama_url}")
            return False

    print("\n" + "=" * 60)
    print("Installation completed successfully!")
    print("=" * 60)
    print("\nThe following models will be used:")
    print("1. Florence-2-large: Watermark detection (auto-downloaded on first use)")
    print(f"2. LaMA: Inpainting/watermark removal (downloaded to {lama_file})")
    print("\nCompatibility notes:")
    print("- The plugin uses lazy imports to avoid startup conflicts")
    print("- It will work with ComfyUI's existing package versions")
    print("- No need to upgrade peft or diffusers")
    print("\nYou can now use the 'Sora Watermark Remover' nodes in ComfyUI!")

    return True

if __name__ == "__main__":
    success = install()
    sys.exit(0 if success else 1)

import torch
import numpy as np
from PIL import Image, ImageDraw
import cv2
from enum import Enum

# Monkey-patch: cached_download was removed in huggingface_hub 0.24, add compatibility shim
import huggingface_hub
if not hasattr(huggingface_hub, 'cached_download'):
    huggingface_hub.cached_download = huggingface_hub.hf_hub_download

# Lazy imports - only import when needed to avoid dependency conflicts at startup
# from transformers import AutoProcessor, Florence2ForConditionalGeneration
# from iopaint.model_manager import ModelManager
# from iopaint.schema import HDStrategy, LDMSampler, InpaintRequest as Config
from loguru import logger

try:
    from cv2.typing import MatLike
except ImportError:
    MatLike = np.ndarray


class TaskType(str, Enum):
    OPEN_VOCAB_DETECTION = "<OPEN_VOCABULARY_DETECTION>"


def download_lama_model():
    """Download LaMA model from GitHub (same as reference project)."""
    from pathlib import Path
    import urllib.request

    logger.info("Downloading LaMA model... (this may take a few minutes)")
    print("Downloading LaMA model (~196MB)... Please wait.")

    # Set up LaMA model paths (same as reference project)
    lama_dir = Path.home() / ".cache" / "torch" / "hub" / "checkpoints"
    lama_file = lama_dir / "big-lama.pt"

    if lama_file.exists():
        logger.info(f"LaMA model already exists at {lama_file}")
        return True

    try:
        lama_dir.mkdir(parents=True, exist_ok=True)
        lama_url = "https://github.com/Sanster/models/releases/download/add_big_lama/big-lama.pt"

        logger.info(f"Downloading from {lama_url}")
        urllib.request.urlretrieve(lama_url, lama_file)

        logger.info("LaMA model downloaded successfully")
        print("LaMA model downloaded!")
        return True
    except Exception as e:
        logger.error(f"Failed to download LaMA model: {e}")
        print(f"Failed to download LaMA model: {e}")
        print("\nYou can download it manually:")
        print(f"  mkdir -p {lama_dir}")
        print(f"  curl -L -o {lama_file} {lama_url}")
        return False


def load_lama_model(device):
    """Load LaMA model, downloading if necessary."""
    # Monkey-patch to bypass peft version check in iopaint
    # This allows iopaint to work with ComfyUI's older peft version (0.7.1)
    import sys

    # Patch both importlib.metadata and importlib_metadata (for compatibility)
    import importlib.metadata
    _original_metadata_version = importlib.metadata.version
    _patched_metadata = []

    try:
        import importlib_metadata
        _original_importlib_metadata_version = importlib_metadata.version
        _patched_metadata.append(('importlib_metadata', _original_importlib_metadata_version))
    except ImportError:
        pass

    def _patched_version(package_name):
        """Return fake version for peft to satisfy iopaint's requirements."""
        if package_name == "peft":
            logger.debug("Bypassing peft version check for iopaint compatibility")
            return "0.17.0"  # Fake version to satisfy iopaint
        return _original_metadata_version(package_name)

    # Apply monkey-patches
    importlib.metadata.version = _patched_version
    if _patched_metadata:
        importlib_metadata.version = _patched_version

    try:
        # Lazy import to avoid dependency conflicts
        from iopaint.model_manager import ModelManager
    except ImportError as e:
        error_msg = (
            f"Failed to import iopaint: {e}\n"
            "Please install iopaint:\n"
            "  pip install iopaint --no-deps\n"
            "Or run the installation script:\n"
            "  cd ComfyUI-JM-Sora-Watermark-Remover && python install.py"
        )
        raise ImportError(error_msg)
    finally:
        # Always restore original version functions
        importlib.metadata.version = _original_metadata_version
        if _patched_metadata:
            importlib_metadata.version = _original_importlib_metadata_version

    # Try to use MPS for LaMA on Apple Silicon, fall back to CPU if unsupported
    lama_device = device  # Try the same device first (including MPS)

    try:
        logger.info(f"Attempting to load LaMA model on {lama_device}...")
        model_manager = ModelManager(name="lama", device=lama_device)
        logger.info(f"✓ LaMA model loaded successfully on {lama_device}")
        return model_manager
    except Exception as e:
        error_msg = str(e)

        # Check if it's a device compatibility error (MPS not supported)
        if lama_device == "mps" and ("mps" in error_msg.lower() or "NotImplementedError" in error_msg):
            logger.warning(f"LaMA doesn't support MPS, falling back to CPU")
            logger.warning(f"(This is a known limitation of IOPaint on Apple Silicon)")
            try:
                model_manager = ModelManager(name="lama", device="cpu")
                logger.info(f"✓ LaMA model loaded on CPU (fallback)")
                return model_manager
            except Exception as cpu_e:
                # Continue to download logic below
                error_msg = str(cpu_e)

        # If model not found, try to download it
        logger.warning(f"LaMA model not found, attempting to download: {error_msg}")
        if download_lama_model():
            try:
                # Retry loading - try original device first, then CPU
                try:
                    return ModelManager(name="lama", device=lama_device)
                except:
                    if lama_device != "cpu":
                        logger.info(f"Falling back to CPU for LaMA")
                        return ModelManager(name="lama", device="cpu")
                    raise
            except Exception as retry_e:
                raise RuntimeError(f"Failed to load LaMA model after download: {retry_e}")
        else:
            raise RuntimeError("Failed to download LaMA model. Please run: python install.py")


def identify(task_prompt: TaskType, image: MatLike, text_input: str, model, processor, device: str):
    """Identify objects using Florence-2 model."""
    if not isinstance(task_prompt, TaskType):
        raise ValueError(f"task_prompt must be a TaskType, but {task_prompt} is of type {type(task_prompt)}")

    prompt = task_prompt.value if text_input is None else task_prompt.value + text_input
    inputs = processor(text=prompt, images=image, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}

    generated_ids = model.generate(
        input_ids=inputs["input_ids"],
        pixel_values=inputs["pixel_values"],
        max_new_tokens=1024,
        do_sample=False,
        num_beams=1,
    )
    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
    return processor.post_process_generation(
        generated_text, task=task_prompt.value, image_size=(image.width, image.height)
    )


def get_watermark_mask(image: MatLike, model, processor, device: str, max_bbox_percent: float, detection_prompt: str = "watermark"):
    """Detect watermarks and create a mask for inpainting."""
    task_prompt = TaskType.OPEN_VOCAB_DETECTION
    parsed_answer = identify(task_prompt, image, detection_prompt, model, processor, device)

    mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(mask)

    detection_key = "<OPEN_VOCABULARY_DETECTION>"
    if detection_key in parsed_answer and "bboxes" in parsed_answer[detection_key]:
        image_area = image.width * image.height
        for bbox in parsed_answer[detection_key]["bboxes"]:
            x1, y1, x2, y2 = map(int, bbox)
            bbox_area = (x2 - x1) * (y2 - y1)
            if (bbox_area / image_area) * 100 <= max_bbox_percent:
                draw.rectangle([x1, y1, x2, y2], fill=255)
            else:
                logger.warning(f"Skipping large bounding box: {bbox} covering {bbox_area / image_area:.2%} of the image")

    return mask


def detect_only(image: MatLike, model, processor, device: str, max_bbox_percent: float, detection_prompt: str = "watermark"):
    """
    Detect watermarks and return bounding boxes WITHOUT creating mask or inpainting.
    Used for sparse detection in video processing.
    """
    task_prompt = TaskType.OPEN_VOCAB_DETECTION
    parsed_answer = identify(task_prompt, image, detection_prompt, model, processor, device)

    results = []
    detection_key = "<OPEN_VOCABULARY_DETECTION>"

    if detection_key in parsed_answer and "bboxes" in parsed_answer[detection_key]:
        image_area = image.width * image.height
        for bbox in parsed_answer[detection_key]["bboxes"]:
            x1, y1, x2, y2 = map(int, bbox)
            bbox_area = (x2 - x1) * (y2 - y1)
            area_percent = (bbox_area / image_area) * 100
            accepted = area_percent <= max_bbox_percent

            if accepted:
                results.append([x1, y1, x2, y2])

    return results


def process_image_with_lama(image: MatLike, mask: MatLike, model_manager, quality_mode="balanced"):
    """Process image with LaMA inpainting model.

    Args:
        image: Input image
        mask: Mask indicating regions to inpaint
        model_manager: LaMA model manager
        quality_mode: Quality/speed tradeoff
            - "fast": ldm_steps=30, faster but lower quality
            - "balanced": ldm_steps=50, good balance (default)
            - "high": ldm_steps=100, slower but better quality
    """
    # Lazy import to avoid dependency conflicts
    from iopaint.schema import HDStrategy, LDMSampler, InpaintRequest as Config

    # Quality presets
    steps_map = {
        "fast": 30,
        "balanced": 50,
        "high": 100,
    }

    ldm_steps = steps_map.get(quality_mode, 50)

    config = Config(
        ldm_steps=ldm_steps,
        ldm_sampler=LDMSampler.ddim,
        hd_strategy=HDStrategy.CROP,
        hd_strategy_crop_margin=128,  # Increased from 64 for better context
        hd_strategy_crop_trigger_size=800,
        hd_strategy_resize_limit=1600,
    )
    result = model_manager(image, mask, config)

    if result.dtype in [np.float64, np.float32]:
        result = np.clip(result, 0, 255).astype(np.uint8)

    return result


def make_region_transparent(image: Image.Image, mask: Image.Image):
    """Make watermark regions transparent."""
    image = image.convert("RGBA")
    mask = mask.convert("L")
    transparent_image = Image.new("RGBA", image.size)
    for x in range(image.width):
        for y in range(image.height):
            if mask.getpixel((x, y)) > 0:
                transparent_image.putpixel((x, y), (0, 0, 0, 0))
            else:
                transparent_image.putpixel((x, y), image.getpixel((x, y)))
    return transparent_image


class SoraWatermarkRemover:
    """ComfyUI node for removing Sora/Sora2 watermarks from images using AI"""

    def __init__(self):
        self.florence_model = None
        self.florence_processor = None
        self.lama_model = None
        # Select device: CUDA > MPS (Apple Silicon) > CPU
        if torch.cuda.is_available():
            self.device = "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "detection_prompt": ("STRING", {
                    "default": "watermark",
                    "multiline": False
                }),
                "max_bbox_percent": ("FLOAT", {
                    "default": 10.0,
                    "min": 0.0,
                    "max": 100.0,
                    "step": 0.1
                }),
            },
            "optional": {
                "transparent": ("BOOLEAN", {
                    "default": False
                }),
                "quality_mode": (["fast", "balanced", "high"], {
                    "default": "balanced"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "remove_watermark"
    CATEGORY = "JM-Nodes/Video/Sora"

    def load_models(self, transparent=False):
        """Load Florence-2 and LaMA models if not already loaded."""
        # Lazy import to avoid dependency conflicts
        try:
            from transformers import AutoProcessor, Florence2ForConditionalGeneration
        except ImportError as e:
            error_msg = (
                f"Failed to import transformers: {e}\n"
                "Please install transformers:\n"
                "  pip install transformers>=4.30.0\n"
                "Or run the installation script:\n"
                "  cd ComfyUI-JM-Sora-Watermark-Remover && python install.py"
            )
            raise ImportError(error_msg)

        if self.florence_model is None:
            logger.info(f"Loading Florence-2 model on {self.device}...")
            logger.info("If this is your first time, Florence-2 model (~1GB) will be downloaded from HuggingFace.")
            logger.info("This may take several minutes depending on your internet connection...")
            logger.info("Model will be cached in ~/.cache/huggingface/hub/ for future use.")

            try:
                self.florence_model = Florence2ForConditionalGeneration.from_pretrained(
                    "florence-community/Florence-2-large"
                ).to(self.device).eval()
                self.florence_processor = AutoProcessor.from_pretrained(
                    "florence-community/Florence-2-large"
                )
                logger.info("Florence-2 model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load Florence-2 model: {e}")
                logger.error("Please check your internet connection or HuggingFace access.")
                raise

        if not transparent and self.lama_model is None:
            logger.info(f"Loading LaMA model on {self.device}...")
            logger.info("LaMA model should be located at ~/.cache/torch/hub/checkpoints/big-lama.pt")

            try:
                self.lama_model = load_lama_model(self.device)
                logger.info("LaMA model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load LaMA model: {e}")
                logger.error("Please ensure LaMA model is downloaded. Run: python install.py")
                raise

    def remove_watermark(self, image, detection_prompt, max_bbox_percent, transparent=False, quality_mode="balanced"):
        """
        Remove watermarks from input image.

        Args:
            image: ComfyUI IMAGE tensor (B, H, W, C) in range [0, 1]
            detection_prompt: Text prompt for watermark detection
            max_bbox_percent: Maximum bbox size as percentage of image
            transparent: Make watermark regions transparent instead of inpainting
            quality_mode: LaMA quality mode ("fast", "balanced", "high")

        Returns:
            Processed IMAGE tensor
        """
        # Load models
        self.load_models(transparent)

        # Process each image in batch
        batch_size = image.shape[0]
        result_images = []

        for i in range(batch_size):
            # Convert ComfyUI tensor to PIL Image
            img_tensor = image[i]
            img_np = (img_tensor.cpu().numpy() * 255).astype(np.uint8)
            pil_image = Image.fromarray(img_np)

            # Get watermark mask
            mask_image = get_watermark_mask(
                pil_image,
                self.florence_model,
                self.florence_processor,
                self.device,
                max_bbox_percent,
                detection_prompt
            )

            # Process image
            if transparent:
                result_image = make_region_transparent(pil_image, mask_image)
                # Convert RGBA to RGB
                background = Image.new("RGB", result_image.size, (255, 255, 255))
                background.paste(result_image, mask=result_image.split()[3])
                result_image = background
            else:
                lama_result = process_image_with_lama(
                    np.array(pil_image),
                    np.array(mask_image),
                    self.lama_model,
                    quality_mode=quality_mode
                )
                result_image = Image.fromarray(cv2.cvtColor(lama_result, cv2.COLOR_BGR2RGB))

            # Convert back to ComfyUI tensor
            result_np = np.array(result_image).astype(np.float32) / 255.0
            result_tensor = torch.from_numpy(result_np)
            result_images.append(result_tensor)

        # Stack batch
        output = torch.stack(result_images)

        return (output,)


class SoraVideoWatermarkRemover:
    """
    ComfyUI node for removing Sora/Sora2 watermarks from video frames using AI.
    Uses two-pass processing with sparse detection for efficiency.
    """

    def __init__(self):
        self.florence_model = None
        self.florence_processor = None
        self.lama_model = None
        # Select device: CUDA > MPS (Apple Silicon) > CPU
        if torch.cuda.is_available():
            self.device = "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "frames": ("IMAGE",),  # Video frames as IMAGE batch
                "detection_prompt": ("STRING", {
                    "default": "watermark",
                    "multiline": False
                }),
                "max_bbox_percent": ("FLOAT", {
                    "default": 10.0,
                    "min": 0.0,
                    "max": 100.0,
                    "step": 0.1
                }),
                "fps": ("FLOAT", {
                    "default": 30.0,
                    "min": 1.0,
                    "max": 120.0,
                    "step": 0.1
                }),
            },
            "optional": {
                "detection_skip": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 10,
                    "step": 1
                }),
                "fade_in": ("FLOAT", {
                    "default": 0.0,
                    "min": 0.0,
                    "max": 10.0,
                    "step": 0.1
                }),
                "fade_out": ("FLOAT", {
                    "default": 0.0,
                    "min": 0.0,
                    "max": 10.0,
                    "step": 0.1
                }),
                "transparent": ("BOOLEAN", {
                    "default": False
                }),
                "quality_mode": (["fast", "balanced", "high"], {
                    "default": "balanced"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "remove_watermark"
    CATEGORY = "JM-Nodes/Video/Sora"

    def load_models(self, transparent=False):
        """Load Florence-2 and LaMA models if not already loaded."""
        # Lazy import to avoid dependency conflicts
        try:
            from transformers import AutoProcessor, Florence2ForConditionalGeneration
        except ImportError as e:
            error_msg = (
                f"Failed to import transformers: {e}\n"
                "Please install transformers:\n"
                "  pip install transformers>=4.30.0\n"
                "Or run the installation script:\n"
                "  cd ComfyUI-JM-Sora-Watermark-Remover && python install.py"
            )
            raise ImportError(error_msg)

        if self.florence_model is None:
            logger.info(f"Loading Florence-2 model on {self.device}...")
            logger.info("If this is your first time, Florence-2 model (~1GB) will be downloaded from HuggingFace.")
            logger.info("This may take several minutes depending on your internet connection...")
            logger.info("Model will be cached in ~/.cache/huggingface/hub/ for future use.")

            try:
                self.florence_model = Florence2ForConditionalGeneration.from_pretrained(
                    "florence-community/Florence-2-large"
                ).to(self.device).eval()
                self.florence_processor = AutoProcessor.from_pretrained(
                    "florence-community/Florence-2-large"
                )
                logger.info("Florence-2 model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load Florence-2 model: {e}")
                logger.error("Please check your internet connection or HuggingFace access.")
                raise

        if not transparent and self.lama_model is None:
            logger.info(f"Loading LaMA model on {self.device}...")
            logger.info("LaMA model should be located at ~/.cache/torch/hub/checkpoints/big-lama.pt")

            try:
                self.lama_model = load_lama_model(self.device)
                logger.info("LaMA model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load LaMA model: {e}")
                logger.error("Please ensure LaMA model is downloaded. Run: python install.py")
                raise

    def remove_watermark(self, frames, detection_prompt, max_bbox_percent, fps,
                        detection_skip=1, fade_in=0.0, fade_out=0.0, transparent=False, quality_mode="balanced"):
        """
        Remove watermarks from video frames using two-pass processing.

        Args:
            frames: ComfyUI IMAGE tensor (B, H, W, C) where B is number of frames
            detection_prompt: Text prompt for watermark detection
            max_bbox_percent: Maximum bbox size as percentage of image
            fps: Frames per second of the video
            detection_skip: Detect watermarks every N frames (1-10)
            fade_in: Extend mask backwards by N seconds for fade-in watermarks
            fade_out: Extend mask forwards by N seconds for fade-out watermarks
            transparent: Make watermark regions transparent instead of inpainting
            quality_mode: LaMA quality mode ("fast", "balanced", "high")

        Returns:
            Processed IMAGE tensor (video frames)
        """
        # Load models
        self.load_models(transparent)

        total_frames = frames.shape[0]
        logger.info(f"Processing video: {total_frames} frames at {fps} fps")

        # Convert seconds to frames
        fade_in_frames = int(fade_in * fps)
        fade_out_frames = int(fade_out * fps)

        logger.info(f"Two-pass processing: skip={detection_skip}, fade_in={fade_in_frames}f, fade_out={fade_out_frames}f")

        # ========== PASS 1: DETECTION (sparse) ==========
        logger.info("Pass 1: Detecting watermarks...")
        detections = {}  # frame_idx -> [bbox, bbox, ...]
        detection_frames = list(range(0, total_frames, detection_skip))

        for frame_idx in detection_frames:
            # Convert frame to PIL Image
            img_tensor = frames[frame_idx]
            img_np = (img_tensor.cpu().numpy() * 255).astype(np.uint8)
            pil_image = Image.fromarray(img_np)

            # Detect watermarks
            bboxes = detect_only(
                pil_image,
                self.florence_model,
                self.florence_processor,
                self.device,
                max_bbox_percent,
                detection_prompt
            )

            if bboxes:
                detections[frame_idx] = bboxes

            if frame_idx % 10 == 0:
                logger.info(f"Pass 1: Detection progress {frame_idx}/{total_frames}")

        logger.info(f"Pass 1 complete: found watermarks in {len(detections)} detection points")

        # ========== TIMELINE EXPANSION ==========
        # Create frame->bbox mapping with fade in/out expansion
        frame_masks = {}  # frame_idx -> [bbox, ...]

        for det_frame, bboxes in detections.items():
            # Expand backwards (fade in)
            start_frame = max(0, det_frame - fade_in_frames)
            # Expand forwards (fade out) + include frames until next detection point
            end_frame = min(total_frames, det_frame + detection_skip + fade_out_frames)

            for f in range(start_frame, end_frame):
                if f not in frame_masks:
                    frame_masks[f] = []
                # Add bboxes, avoiding duplicates
                for bbox in bboxes:
                    if bbox not in frame_masks[f]:
                        frame_masks[f].append(bbox)

        logger.info(f"Timeline expanded: {len(frame_masks)} frames will have inpainting applied")

        # ========== PASS 2: INPAINTING ==========
        logger.info("Pass 2: Applying inpainting...")
        result_frames = []

        for frame_idx in range(total_frames):
            img_tensor = frames[frame_idx]
            img_np = (img_tensor.cpu().numpy() * 255).astype(np.uint8)
            pil_image = Image.fromarray(img_np)

            if frame_idx in frame_masks:
                # This frame needs inpainting
                # Create mask from bboxes
                mask = Image.new("L", pil_image.size, 0)
                draw = ImageDraw.Draw(mask)
                for bbox in frame_masks[frame_idx]:
                    x1, y1, x2, y2 = bbox
                    draw.rectangle([x1, y1, x2, y2], fill=255)

                # Apply inpainting or transparency
                if transparent:
                    result_image = make_region_transparent(pil_image, mask)
                    background = Image.new("RGB", result_image.size, (255, 255, 255))
                    background.paste(result_image, mask=result_image.split()[3])
                    result_image = background
                else:
                    lama_result = process_image_with_lama(
                        np.array(pil_image),
                        np.array(mask),
                        self.lama_model,
                        quality_mode=quality_mode
                    )
                    result_image = Image.fromarray(cv2.cvtColor(lama_result, cv2.COLOR_BGR2RGB))
            else:
                # No watermark, keep original
                result_image = pil_image

            # Convert to tensor
            result_np = np.array(result_image).astype(np.float32) / 255.0
            result_tensor = torch.from_numpy(result_np)
            result_frames.append(result_tensor)

            if frame_idx % 10 == 0:
                logger.info(f"Pass 2: Inpainting progress {frame_idx}/{total_frames}")

        # Stack all frames
        output = torch.stack(result_frames)

        logger.info(f"Video processing complete: {total_frames} frames processed")
        return (output,)


NODE_CLASS_MAPPINGS = {
    "SoraWatermarkRemover": SoraWatermarkRemover,
    "SoraVideoWatermarkRemover": SoraVideoWatermarkRemover,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SoraWatermarkRemover": "Sora Watermark Remover (Image)",
    "SoraVideoWatermarkRemover": "Sora Watermark Remover (Video)",
}

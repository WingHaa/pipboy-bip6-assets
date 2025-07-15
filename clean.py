import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

input_dir = "./thumbs_up/"
output_dir = "processed"
os.makedirs(output_dir, exist_ok=True)

trim_width = 0
trim_height = 0
target_size = (112, 196)

def apply_pipboy_glow(image_path: str, output_path: str):
    img = Image.open(image_path).convert("RGBA")
    data = np.array(img)

    alpha = data[..., 3]
    white_mask = (data[..., 0:3] > 200).all(axis=-1) & (alpha > 0)

    data[..., 0] = np.where(white_mask, 134, data[..., 0])
    data[..., 1] = np.where(white_mask, 254, data[..., 1])
    data[..., 2] = np.where(white_mask, 0, data[..., 2])

    img = Image.fromarray(data).convert("RGBA")

    # Optional glow blur
    img = img.filter(ImageFilter.GaussianBlur(radius=1))

    # Create a scanline image for the whole image
    scanline_overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(scanline_overlay)
    for y in range(0, img.height, 4):
        draw.line((0, y, img.width, y), fill=(0, 0, 0, 16))

    # Apply mask to restrict scanlines to only green area
    mask = Image.fromarray((white_mask * 255).astype(np.uint8)).convert('L')

    # Apply the mask to the scanlines
    scanline_overlay_masked = Image.composite(scanline_overlay, Image.new("RGBA", img.size, (0, 0, 0, 0)), mask)

    img = Image.alpha_composite(img, scanline_overlay_masked)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path)

# Step 1: Trim transparent edges & track largest width/height
for fname in os.listdir(input_dir):
    if not fname.lower().endswith(".png"):
        continue

    path = os.path.join(input_dir, fname)
    img = Image.open(path).convert("RGBA")
    alpha = np.array(img)[..., 3]

    ys, xs = np.where(alpha > 0)
    if len(xs) == 0 or len(ys) == 0:
        print(f"⚠️ Skipping transparent: {fname}")
        continue

    left, right = int(np.min(xs)), int(np.max(xs))
    top, bottom = int(np.min(ys)), int(np.max(ys))

    width, height = img.size
    center_x = int(width / 2)
    center_y = int(height / 2)

    current_trim_width = 2 * max(center_x - left, right - center_x)
    current_trim_height = 2 * max(center_y - top, bottom - center_y)
    trim_width = max(current_trim_width, trim_width)
    trim_height = max(current_trim_height, trim_height)

print(f"📏 Max sprite dimensions after trim: {trim_width} × {trim_height}")

# STEP 2: Crop center → Resize → Pad
for fname in os.listdir(input_dir):
    if not fname.lower().endswith(".png"):
        continue

    path = os.path.join(input_dir, fname)
    output_path = os.path.join(output_dir, fname)
    img = Image.open(path).convert("RGBA")
    width, height = img.size
    center_x = width // 2
    center_y = height // 2

    # Compute box centered at (center_x, center_y)
    left = max(center_x - trim_width // 2, 0)
    top = max(center_y - trim_height // 2, 0)
    right = min(center_x + trim_width // 2, width)
    bottom = min(center_y + trim_height // 2, height)

    cropped = img.crop((left, top, right, bottom))

    # Resize based on trim proportions
    if trim_width > trim_height:
        scale_w = target_size[0]
        scale_h = int(scale_w * cropped.height / cropped.width)
    else:
        scale_h = target_size[1]
        scale_w = int(scale_h * cropped.width / cropped.height)

    resized = cropped.copy()
    resized.thumbnail(target_size, Image.Resampling.LANCZOS)

    # Pad to final target size (112×196)
    canvas = Image.new("RGBA", target_size, (0, 0, 0, 0))
    offset_x = (target_size[0] - resized.width) // 2
    offset_y = (target_size[1] - resized.height) // 2
    canvas.paste(resized, (offset_x, offset_y))
    canvas.save(output_path)

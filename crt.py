import os

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter


def apply_pipboy_glow(image_path, output_path):
    img = Image.open(image_path).convert("RGBA")
    data = np.array(img)

    # Extract alpha channel
    alpha = data[..., 3]

    # Create green-tinted version only where image is white-ish (non-transparent)
    white_mask = (data[..., 0:3] > 200).all(axis=-1) & (alpha > 0)

    # Replace color with green (Pip-Boy style)
    data[..., 0] = np.where(white_mask, 134, data[..., 0])      # Red → 0
    data[..., 1] = np.where(white_mask, 254, data[..., 1])    # Green → 255
    data[..., 2] = np.where(white_mask, 0, data[..., 2])      # Blue → 0

    img = Image.fromarray(data).convert("RGBA")

    # Slight glow blur (optional)
    img = img.filter(ImageFilter.GaussianBlur(radius=1))

    # Add scanlines (on top of green part only)
    scanline_overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(scanline_overlay)
    for y in range(0, img.height, 4):
        draw.line((0, y, img.width, y), fill=(0, 0, 0, 16))  # semi-transparent lines

    img = Image.alpha_composite(img, scanline_overlay)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path)


base_dir = "./processed/"
output_base = "./pipboyified"

for root, dirs, files in os.walk(base_dir):
    for file in files:
        if file.lower().endswith(".png"):
            input_path = os.path.join(root, file)
            # Skip the output directory itself
            if output_base in input_path:
                continue
            rel_path = os.path.relpath(input_path, base_dir)
            output_path = os.path.join(output_base, rel_path)
            apply_pipboy_glow(input_path, output_path)

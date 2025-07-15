import os

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

def apply_pipboy_glow(image_path, output_path):
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
    # Convert white_mask to PIL Image in 'L' mode
    mask = Image.fromarray((white_mask * 255).astype(np.uint8)).convert('L')

    # Apply the mask to the scanlines
    scanline_overlay_masked = Image.composite(scanline_overlay, Image.new("RGBA", img.size, (0, 0, 0, 0)), mask)

    img = Image.alpha_composite(img, scanline_overlay_masked)

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

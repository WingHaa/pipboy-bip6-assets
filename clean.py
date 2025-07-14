import os
import numpy as np
from PIL import Image

input_dir = "./thumbs_up/"
output_dir = "processed"
os.makedirs(output_dir, exist_ok=True)

max_trimmed_width = 0
max_trimmed_height = 0
cropped_images = []
target_size = (112, 196)

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

    left, right = np.min(xs), np.max(xs)
    top, bottom = np.min(ys), np.max(ys)

    cropped = img.crop((left, top, right + 1, bottom + 1))
    cropped_images.append((fname, cropped))

    w, h = cropped.size
    max_trimmed_width = max(max_trimmed_width, w)
    max_trimmed_height = max(max_trimmed_height, h)

print(f"📏 Max sprite dimensions after trim: {max_trimmed_width} × {max_trimmed_height}")

# Step 2: Resize and pad to 112×196 while preserving alignment
for fname, cropped in cropped_images:
    # Resize proportionally
    cropped.thumbnail(target_size, Image.Resampling.LANCZOS)

    # Create canvas and center image
    canvas = Image.new("RGBA", target_size, (0, 0, 0, 0))
    offset = (
        (target_size[0] - cropped.width) // 2,
        (target_size[1] - cropped.height) // 2
    )
    canvas.paste(cropped, offset)

    output_path = os.path.join(output_dir, fname)
    canvas.save(output_path)
    print(f"✅ Saved: {output_path}")

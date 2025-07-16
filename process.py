import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

target_size = (112, 196)

def trim_and_get_max_dims(images):
    trim_width = 0
    trim_height = 0
    trim_info = {}

    for image_path in images:
        img = Image.open(image_path).convert("RGBA")
        alpha = np.array(img)[..., 3]

        ys, xs = np.where(alpha > 0)
        if len(xs) == 0 or len(ys) == 0:
            continue

        left, right = int(np.min(xs)), int(np.max(xs))
        top, bottom = int(np.min(ys)), int(np.max(ys))

        width, height = img.size
        center_x = int(width / 2)
        center_y = int(height / 2)

        current_trim_width = 2 * max(center_x - left, right - center_x)
        current_trim_height = 2 * max(center_y - top, bottom - center_y)

        trim_width = max(trim_width, current_trim_width)
        trim_height = max(trim_height, current_trim_height)
        trim_info[image_path] = (width, height, center_x, center_y)

    return trim_width, trim_height, trim_info


def crop_resize_pad(image_path, trim_width, trim_height):
    img = Image.open(image_path).convert("RGBA")
    width, height = img.size
    center_x = width // 2
    center_y = height // 2

    left = max(center_x - trim_width // 2, 0)
    top = max(center_y - trim_height // 2, 0)
    right = min(center_x + trim_width // 2, width)
    bottom = min(center_y + trim_height // 2, height)

    cropped = img.crop((left, top, right, bottom))
    target_height = 196
    orig_w, orig_h = cropped.size
    new_w = int((target_height / orig_h) * orig_w)

    return cropped.resize((new_w, target_height), Image.Resampling.LANCZOS)


def apply_pipboy_glow(img):
    data = np.array(img)
    alpha = data[..., 3]
    white_mask = (data[..., 0:3] > 200).all(axis=-1) & (alpha > 0)

    data[..., 0] = np.where(white_mask, 134, data[..., 0])
    data[..., 1] = np.where(white_mask, 254, data[..., 1])
    data[..., 2] = np.where(white_mask, 0, data[..., 2])

    img = Image.fromarray(data).convert("RGBA")
    img = img.filter(ImageFilter.GaussianBlur(radius=1))

    scanline_overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(scanline_overlay)
    for y in range(0, img.height, 4):
        draw.line((0, y, img.width, y), fill=(0, 0, 0, 16))

    mask = Image.fromarray((white_mask * 255).astype(np.uint8)).convert('L')
    masked_lines = Image.composite(scanline_overlay, Image.new("RGBA", img.size, (0, 0, 0, 0)), mask)

    return Image.alpha_composite(img, masked_lines)


def process_all_images(base_dir="."):
    for folder_name in os.listdir(base_dir):
        folder_path = os.path.join(base_dir, folder_name)
        if not os.path.isdir(folder_path) or folder_name.startswith("."):
            continue

        images = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith(".png")]
        if not images:
            continue

        trim_width, trim_height, _ = trim_and_get_max_dims(images)
        output_subdir = os.path.join("pipboyfied", folder_name)
        os.makedirs(output_subdir, exist_ok=True)

        for i, img_path in enumerate(sorted(images)):
            processed = crop_resize_pad(img_path, trim_width, trim_height)
            glowing = apply_pipboy_glow(processed)
            output_file = os.path.join(output_subdir, f"anim_{i}.png")
            glowing.save(output_file)

        print(f"✅ Processed {len(images)} image(s) → {output_subdir}")

if __name__ == "__main__":
    process_all_images()

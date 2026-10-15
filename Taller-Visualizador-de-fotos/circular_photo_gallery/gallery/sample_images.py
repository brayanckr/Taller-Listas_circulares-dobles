"""Generate placeholder pictures with Pillow so the app works on first run."""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFont

# (title, description, top color, bottom color)
SAMPLES: List[Tuple[str, str, Tuple[int, int, int], Tuple[int, int, int]]] = [
    ("Sunrise Valley", "Warm light spilling over a quiet valley.", (255, 150, 79), (255, 213, 107)),
    ("Ocean Breeze", "Calm blue water under a clear sky.", (28, 116, 190), (120, 207, 230)),
    ("Pine Forest", "Tall pines in the early morning fog.", (21, 87, 66), (110, 190, 140)),
    ("Violet Dusk", "The sky fading into purple after sunset.", (88, 52, 150), (232, 120, 176)),
    ("Desert Dunes", "Golden dunes stretching to the horizon.", (196, 120, 50), (245, 205, 130)),
    ("Arctic Ice", "Pale ice fields under a winter sky.", (90, 140, 190), (225, 240, 250)),
    ("Cherry Blossom", "Pink petals falling in a spring garden.", (214, 90, 140), (255, 205, 220)),
    ("Midnight City", "City lights glowing against the night.", (15, 20, 50), (70, 80, 140)),
]

WIDTH, HEIGHT = 960, 640


def _load_font(size: int) -> ImageFont.ImageFont:
    """Return a TrueType font when available, otherwise Pillow's default."""
    for name in ("arial.ttf", "DejaVuSans.ttf", "Helvetica.ttc"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def _make_image(title: str, top: Tuple[int, int, int], bottom: Tuple[int, int, int]) -> Image.Image:
    """Draw a vertical gradient with decorative circles and a title."""
    image = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(image)
    for y in range(HEIGHT):
        ratio = y / (HEIGHT - 1)
        color = tuple(int(top[i] + (bottom[i] - top[i]) * ratio) for i in range(3))
        draw.line([(0, y), (WIDTH, y)], fill=color)
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    odraw.ellipse([620, -120, 1100, 360], fill=(255, 255, 255, 45))
    odraw.ellipse([-140, 360, 360, 820], fill=(255, 255, 255, 35))
    odraw.ellipse([380, 250, 560, 430], fill=(255, 255, 255, 60))
    image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(image)
    font = _load_font(64)
    box = draw.textbbox((0, 0), title, font=font)
    x = (WIDTH - (box[2] - box[0])) / 2
    y = HEIGHT - 150
    draw.text((x + 3, y + 3), title, font=font, fill=(0, 0, 0))
    draw.text((x, y), title, font=font, fill=(255, 255, 255))
    return image


def generate_sample_images(target_dir: Path) -> List[Tuple[str, str, str]]:
    """Create the sample pictures inside ``target_dir``.

    Returns:
        A list of ``(title, description, filename)`` tuples, one per picture.
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    created: List[Tuple[str, str, str]] = []
    for index, (title, description, top, bottom) in enumerate(SAMPLES, start=1):
        filename = f"sample_{index:02d}.png"
        path = target_dir / filename
        if not path.exists():
            _make_image(title, top, bottom).save(path)
        created.append((title, description, filename))
    return created

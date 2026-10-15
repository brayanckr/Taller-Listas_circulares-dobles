"""Initial demo data: SVG placeholder car renders generated as data URIs."""
import math
from urllib.parse import quote

SEED_FRAMES = (
    (0, "Aggressive front fascia with LED headlights."),
    (60, "Front three-quarter view showing the hood line."),
    (120, "Rear three-quarter view highlighting the roofline."),
    (180, "Rear view with full-width tail lights."),
    (240, "Rear left three-quarter view."),
    (300, "Front left three-quarter view."),
)


def build_car_svg(angle_degree):
    """Stylised car whose visible width follows the viewing angle."""
    rad = math.radians(angle_degree)
    side = abs(math.sin(rad))  # 1 = pure side view, 0 = front/rear
    facing_front = math.cos(rad) >= 0
    width = 140 + 280 * side
    left = 300 - width / 2
    cabin_w = width * 0.55
    cabin_x = 300 - cabin_w / 2 + math.sin(rad) * 30
    lamp = "#fde047" if facing_front else "#b91c1c"
    wheel_gap = max(width * 0.55, 90)
    radius = 20 + 14 * side

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 360">',
        '<rect width="600" height="360" fill="#1e293b"/>',
        f'<ellipse cx="300" cy="288" rx="{width / 2 + 20:.0f}" ry="14" fill="#000" opacity=".4"/>',
        f'<path d="M{cabin_x:.0f} 170 L{cabin_x + 30:.0f} 120 L{cabin_x + cabin_w - 30:.0f} 120 '
        f'L{cabin_x + cabin_w:.0f} 170 Z" fill="#38bdf8" opacity=".85"/>',
        f'<rect x="{left:.0f}" y="165" width="{width:.0f}" height="95" rx="22" fill="#ef4444"/>',
    ]
    if side < 0.6:
        for lx in (left + 14, left + width - 48):
            parts.append(f'<rect x="{lx:.0f}" y="190" width="34" height="16" rx="6" fill="{lamp}"/>')
    else:
        edge = left + width - 22 if (math.sin(rad) > 0) == facing_front else left + 8
        parts.append(f'<rect x="{edge:.0f}" y="190" width="14" height="16" rx="5" fill="{lamp}"/>')
    for wx in (300 - wheel_gap / 2, 300 + wheel_gap / 2):
        parts.append(f'<circle cx="{wx:.0f}" cy="262" r="{radius:.0f}" fill="#111827"/>')
        parts.append(f'<circle cx="{wx:.0f}" cy="262" r="{radius * 0.45:.0f}" fill="#9ca3af"/>')
    parts.append(
        '<text x="300" y="338" text-anchor="middle" font-family="sans-serif" '
        f'font-size="22" fill="#cbd5e1">{angle_degree}°</text>'
    )
    parts.append("</svg>")
    return "".join(parts)


def svg_data_uri(svg):
    return "data:image/svg+xml;utf8," + quote(svg)


def load_seed_frames(frame_list):
    for angle, description in SEED_FRAMES:
        frame_list.insert_frame(angle, svg_data_uri(build_car_svg(angle)), description)

#!/usr/bin/env python3
"""Render one comparison card from the theme files themselves.

Left column: the light theme. Right column: the dark one. Every chip and
hex is read from themes/*.json — nothing here is a screenshot.
"""

import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / ".github"

LIGHT = "z1-ocean"
DARK = "z1-default"

# The same roles in both columns, so the two themes can be read against
# each other.
ROLES = [
    ("background", "editor.background"),
    ("text", "editor.foreground"),
    ("muted", "tab.inactiveForeground"),
    ("accent", "button.background"),
    ("selection", "list.activeSelectionBackground"),
    ("hover", "list.hoverBackground"),
    ("border", "editorGroup.border"),
    ("status bar", "statusBar.background"),
]


def load(name):
    theme = json.loads((ROOT / "themes" / f"{name}.json").read_text())
    return theme


def shown(value, base):
    """Translucent colours as the eye sees them, over this theme's own surface."""
    if len(value) == 9:
        alpha = int(value[7:9], 16) / 255
        rgb = [int(value[i:i + 2], 16) for i in (1, 3, 5)]
        under = [int(base[i:i + 2], 16) for i in (1, 3, 5)]
        return "#%02X%02X%02X" % tuple(round(c * alpha + u * (1 - alpha)) for c, u in zip(rgb, under))
    if value.upper() == "#00000000":
        return base
    return value.upper()


def column(theme, x, width, ink, dim, line, label, kind):
    colors = theme["colors"]
    base = colors["editor.background"]
    body = [
        f'<text x="{x + 40}" y="76" font-family="monospace" font-size="30" '
        f'fill="{ink}">{theme["name"]}</text>',
        f'<text x="{x + 40}" y="102" font-family="monospace" font-size="13" '
        f'fill="{dim}">{kind}</text>',
    ]
    y = 140
    for role, key in ROLES:
        value = shown(colors.get(key, "#000000"), base)
        body.append(
            f'<rect x="{x + 40}" y="{y}" width="56" height="56" fill="{value}" '
            f'stroke="{line}"/>'
        )
        body.append(
            f'<text x="{x + 116}" y="{y + 24}" font-family="monospace" font-size="15" '
            f'fill="{ink}">{role}</text>'
        )
        body.append(
            f'<text x="{x + 116}" y="{y + 46}" font-family="monospace" font-size="13" '
            f'fill="{dim}">{value}</text>'
        )
        body.append(
            f'<rect x="{x + 40}" y="{y + 70}" width="{width - 80}" height="1" fill="{line}"/>'
        )
        y += 84
    return body, y


def main():
    light = load(LIGHT)
    dark = load(DARK)

    width = 1120
    left_w = 560
    rows = len(ROLES)
    height = 140 + rows * 84 + 24

    light_body, light_end = column(
        light, 0, left_w, "#000000", "#8A8A8A", "#EAEAEA", "light", "light \u00b7 white surfaces"
    )
    dark_body, dark_end = column(
        dark, left_w, width - left_w, "#FFFFFF", "#9A9A9A", "#2E2E2E", "dark", "dark \u00b7 neutral surfaces"
    )

    body = [
        f'<rect x="0" y="0" width="{left_w}" height="{height}" fill="#FFFFFF"/>',
        f'<rect x="{left_w}" y="0" width="{width - left_w}" height="{height}" fill="{dark["colors"]["editor.background"]}"/>',
        f'<rect x="{left_w}" y="0" width="1" height="{height}" fill="#E0E0E0"/>',
        *light_body,
        *dark_body,
    ]

    svg = OUT / "compare.svg"
    svg.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n' + "\n".join(body) + "</svg>\n"
    )
    subprocess.run(["rsvg-convert", "-w", str(width * 2), str(svg), "-o", str(OUT / "compare.png")], check=True)
    print(f"compare: {width}x{height}")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    main()

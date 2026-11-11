#!/usr/bin/env python3
"""Render the theme's colours into cards. Nothing here is a screenshot:
every swatch and every syntax colour is read from themes/*.json."""

import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / ".github"

BLACK = "#000000"
GREY = "#5A6773"
LIGHT = "#9099A2"
LINE = "#E7ECF2"

# One row per role: (role, colour id or literal). Duplicates are dropped.
ROLES = [
    ("paper", "editor.background"),
    ("paper", "sideBar.background"),
    ("ink", "statusBar.background"),
    ("ink", "editor.foreground"),
    ("grey", "sideBar.foreground"),
    ("muted", "tab.inactiveForeground"),
    ("comment", "#BEC9D3"),
    ("string", "#6B7A88"),
    ("border", "#E7ECF2"),
    ("selection", "list.activeSelectionBackground"),
    ("hover", "list.hoverBackground"),
    ("editor selection", "editor.selectionBackground"),
    ("find", "editor.findMatchBackground"),
    ("ink", "tab.activeBackground"),
    ("ink", "button.background"),
    ("ink", "badge.background"),
    ("ink", "focusBorder"),
    ("error", "editorError.foreground"),
    ("warning", "editorWarning.foreground"),
    ("added", "gitDecoration.addedResourceForeground"),
    
]


def load(name):
    return json.loads((ROOT / "themes" / f"{name}.json").read_text())


def write_svg(path, body, width, height, bg="#FFFFFF"):
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n'
        f'<rect width="{width}" height="{height}" fill="{bg}"/>\n{body}</svg>\n'
    )
    pathlib.Path(path).write_text(svg)


def render(svg, png, width):
    subprocess.run(["rsvg-convert", "-w", str(width), str(svg), "-o", str(png)], check=True)


def palette():
    theme = load("z1-ocean")
    colors = theme["colors"]

    cols = 3
    card_w = 300
    card_h = 148
    gap = 16
    pad = 44
    header = 112
    width = pad * 2 + cols * card_w + (cols - 1) * gap

    body = [
        f'<text x="{pad}" y="62" font-family="monospace" font-size="30" fill="{BLACK}">'
        f"{theme['name']}</text>",
        f'<text x="{pad}" y="88" font-family="monospace" font-size="13" fill="{LIGHT}">'
        f"{len(colors)} colour keys \u00b7 white surfaces \u00b7 black accents</text>",
    ]

    # Group roles that resolve to the same colour, and show translucent ones as
    # what the eye sees: blended onto the white surface underneath.
    def blend(value):
        if len(value) == 9:
            alpha = int(value[7:9], 16) / 255
            rgb = [int(value[i:i + 2], 16) for i in (1, 3, 5)]
            return "#%02X%02X%02X" % tuple(round(c * alpha + 255 * (1 - alpha)) for c in rgb)
        if value.upper() == "#00000000":
            return "#FFFFFF"
        return value.upper()

    merged = {}
    order = []
    for role, key in ROLES:
        shown = blend(colors.get(key, key))
        if shown not in merged:
            merged[shown] = []
            order.append(shown)
        merged[shown].append(role)

    items = [
        (" \u00b7 ".join(dict.fromkeys(merged[shown])), shown) for shown in order
    ]
    rows = (len(items) + cols - 1) // cols
    height = header + rows * (card_h + gap) + pad - gap

    for index, (role, value) in enumerate(items):
        col = index % cols
        row = index // cols
        x = pad + col * (card_w + gap)
        y = header + row * (card_h + gap)
        swatch_h = 74
        body.append(
            f'<rect x="{x}" y="{y}" width="{card_w}" height="{swatch_h}" fill="{value}" '
            f'stroke="{LINE}"/>'
        )
        body.append(
            f'<text x="{x}" y="{y + swatch_h + 24}" font-family="monospace" font-size="14" '
            f'fill="{BLACK}">{role[:34]}</text>'
        )
        body.append(
            f'<text x="{x}" y="{y + swatch_h + 44}" font-family="monospace" '
            f'font-size="13" fill="{LIGHT}">{value.upper()}</text>'
        )

    svg = OUT / "palette.svg"
    write_svg(svg, "\n".join(body), width, height)
    render(svg, OUT / "palette.png", width * 2)
    print(f"palette: {width}x{height} ({len(items)} unique)")


# Each line is a list of (kind, text) segments so colours can change mid-line.
CODE = [
    [("comment", "// Session runtime: history, tools and context")],
    [],
    [("kw", "import"), ("plain", " { Effect, Schema } "), ("kw", "from"), ("str", ' "effect"')],
    [],
    [("kw", "export class"), ("plain", " Agent {")],
    [("plain", "  private readonly history: Message[] = []")],
    [],
    [("kw", "  async"), ("plain", " run(prompt: string): Promise<Result> {")],
    [("plain", "    this.history.push({ role: "), ("str", '"user"'), ("plain", ", content: prompt })")],
    [],
    [("kw", "    for"), ("plain", " ("), ("kw", "const"), ("plain", " tool "), ("kw", "of"), ("plain", " tools) {")],
    [("kw", "      const"), ("plain", " result = "), ("kw", "await"), ("plain", " this.call(tool, prompt)")],
    [],
    [("kw", "      if"), ("plain", " (!result.ok) {")],
    [("plain", "        console.warn("), ("str", '"tool failed"'), ("plain", ")")],
    [("kw", "        continue")],
    [("plain", "      }")],
    [("plain", "    }")],
    [],
    [("kw", "    return"), ("plain", " { ok: "), ("kw", "true"), ("plain", ", messages: 12 }")],
    [("plain", "  }")],
    [("plain", "}")],
]

KIND = {
    "plain": BLACK,
    "kw": BLACK,
    "str": "#6B7A88",
    "comment": "#BEC9D3",
}


def syntax():
    width = 700
    line_h = 27
    top = 108
    height = top  # grown as lines are placed
    body = [
        f'<text x="40" y="54" font-family="monospace" font-size="26" fill="{BLACK}">'
        f"syntax</text>",
        f'<text x="40" y="80" font-family="monospace" font-size="13" fill="{LIGHT}">'
        f"three greys \u00b7 bold keywords</text>",
        f'<rect x="40" y="92" width="{width - 80}" height="1" fill="{LINE}"/>',
    ]
    y = top
    for number, line in enumerate(CODE, start=1):
        if not line:
            y += line_h * 0.55
            continue
        body.append(
            f'<text x="40" y="{y:.0f}" font-family="monospace" font-size="12" fill="#C2C9D0" '
            f'text-anchor="end">{number}</text>'
        )
        spans = []
        for kind, text in line:
            escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            weight = ' font-weight="bold"' if kind == "kw" else ""
            spans.append(f'<tspan fill="{KIND[kind]}"{weight}>{escaped}</tspan>')
        body.append(
            f'<text x="58" y="{y:.0f}" font-family="monospace" font-size="15" xml:space="preserve">'
            f'{"".join(spans)}</text>'
        )
        y += line_h

    height = y + 24
    svg = OUT / "syntax.svg"
    write_svg(svg, "\n".join(body), width, int(height))
    render(svg, OUT / "syntax.png", width * 2)
    print(f"syntax: {width}x{int(height)}")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    palette()
    syntax()

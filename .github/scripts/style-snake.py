#!/usr/bin/env python3
import re
import sys

SNAKE_SIZES = (10.0, 8.5, 7.5, 6.5)
BACKGROUNDS = {"light": "#f8fafc", "dark": "#0b1026"}


def style(svg, background):
    for index, size in enumerate(SNAKE_SIZES):
        offset = 8 - size / 2
        radius = size / 3
        svg = re.sub(
            rf'<rect class="s s{index}"[^>]*/>',
            f'<rect class="s s{index}" x="{offset:.2f}" y="{offset:.2f}" '
            f'width="{size}" height="{size}" rx="{radius:.2f}" ry="{radius:.2f}"/>',
            svg,
        )

    svg = re.sub(
        r'<svg viewBox="[^"]*" width="\d+" height="\d+"',
        '<svg viewBox="-16 -40 880 176" width="860" height="172"',
        svg,
        count=1,
    )
    frame = (
        '<defs><linearGradient id="edge" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#38bdf8"/><stop offset=".5" stop-color="#a78bfa"/>'
        '<stop offset="1" stop-color="#34d399"/></linearGradient></defs>'
        f'<rect x="-15" y="-39" width="878" height="174" rx="6" fill="{background}" '
        'stroke="url(#edge)" stroke-width="2"/>'
    )
    return re.sub(r"(</style>)", rf"\1{frame}", svg, count=1)


def main():
    for path, theme in zip(sys.argv[1::2], sys.argv[2::2]):
        with open(path, encoding="utf-8") as svg_file:
            svg = svg_file.read()
        with open(path, "w", encoding="utf-8") as svg_file:
            svg_file.write(style(svg, BACKGROUNDS[theme]))


if __name__ == "__main__":
    main()

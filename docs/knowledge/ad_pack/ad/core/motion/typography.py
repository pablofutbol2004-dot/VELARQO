"""Typography estimation for the motion compile engine + pre-render QC.

The renderer (Remotion/React) measures real glyphs at render time; the compiler
cannot run browser layout first, so these conservative estimators are the shared
source of truth that both ``compile`` (to lay text out) and ``qc`` (to verify it)
use. They must agree, or QC would reject the compiler's own output.
"""

from __future__ import annotations

#: Average glyph advance as a fraction of font size (conservative; Inter/Archivo).
GLYPH_WIDTH = 0.52
#: Line box advance as a fraction of font size.
LINE_HEIGHT = 1.16
#: Short-form on-screen reading speed (words per minute). Proven fixture
#: durations (~2.2s for a 6-11 word hook) sit close to this cadence.
READING_WPM = 300


def wrap_lines(text: str, *, font_size: float, width: float) -> list[str]:
    """Split ``text`` into lines that fit ``width`` at ``font_size``.

    Deterministic greedy word wrap; an over-long token is hard-broken so no line
    can overflow the box (conservative — the real renderer may wrap tighter).
    """
    text = " ".join(str(text).split())
    if not text:
        return []
    chars_per_line = max(1, int(width / (GLYPH_WIDTH * font_size)))
    lines: list[str] = []
    current = ""
    for token in text.split(" "):
        # Hard-break a token longer than a full line.
        while len(token) > chars_per_line:
            chunk, token = token[:chars_per_line], token[chars_per_line:]
            if current:
                lines.append(current)
                current = ""
            lines.append(chunk)
        if not token:
            continue
        candidate = f"{current} {token}".strip()
        if current and len(candidate) > chars_per_line:
            lines.append(current)
            current = token
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def block_height(lines: list[str], *, font_size: float) -> float:
    """Estimated rendered height (px) of a wrapped text block."""
    return len(lines) * font_size * LINE_HEIGHT


def line_px(line: str, *, font_size: float) -> float:
    """Estimated rendered width (px) of one wrapped line."""
    return max(1, len(line)) * GLYPH_WIDTH * font_size


def reading_time_seconds(text: str) -> float:
    """How long a short on-screen line needs to be read (seconds)."""
    words = len([w for w in str(text).split() if w])
    return words * 60.0 / READING_WPM


def lighten(color: str, amount: float) -> str:
    """Blend a hex color toward white by ``amount`` (0..1); deterministic."""
    r, g, b = hex_to_rgb(color)
    mix = min(1.0, max(0.0, amount))
    blended = tuple(round(c + (255 - c) * mix) for c in (r, g, b))
    return "#{:02X}{:02X}{:02X}".format(*blended)


def hex_to_rgb(color: str) -> tuple[int, int, int]:
    """Parse ``#RRGGBB`` (loudly) — QC only checks authored hex colors."""
    value = str(color).lstrip("#")
    if len(value) != 6:
        raise ValueError(f"expected a #RRGGBB color, got {color!r}")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _luminance(rgb: tuple[int, int, int]) -> float:
    def channel(c: float) -> float:
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = rgb
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def contrast_ratio(fg: str, bg: str) -> float:
    """WCAG contrast ratio between two hex colors."""
    l1, l2 = _luminance(hex_to_rgb(fg)), _luminance(hex_to_rgb(bg))
    lighter, darker = (l1, l2) if l1 > l2 else (l2, l1)
    return (lighter + 0.05) / (darker + 0.05)

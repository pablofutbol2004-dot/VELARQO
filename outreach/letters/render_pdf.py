"""Print-ready A4 letters (one page each) from data/letters_batch1.csv.

Free libraries only: reportlab (PDF) and qrcode (QR code). Fonts: Georgia if
present on the machine (Windows ships it), otherwise Times.

Address block sits in the usual hybrid-mail window zone (left 25 mm, 45-85 mm from
the top). Check it against the chosen printer's template before ordering.

Usage:
  python -m outreach.letters.render_pdf                         # all rows -> data/letters/batch1/
  python -m outreach.letters.render_pdf --sample docs/letters/sample_letter.pdf
  python -m outreach.letters.render_pdf --csv data/letters_batch1.csv --out data/letters/batch1
Options: --photo path.jpg  --signature path.png  --date 2026-10-27
"""
from __future__ import annotations

import argparse
import csv
import io
import os
import re
from datetime import date
from pathlib import Path

import qrcode
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Frame, Paragraph, Spacer
from reportlab.lib.utils import ImageReader

from outreach.letters import letter_text as lt

W, H = A4
LEFT, RIGHT, TOP, BOTTOM = 25 * mm, 22 * mm, 18 * mm, 16 * mm
CORAL = (0.90, 0.30, 0.25)
INK = (0.10, 0.10, 0.10)
GREY = (0.45, 0.45, 0.45)


def _fonts() -> tuple[str, str, str]:
    """(regular, bold, italic) font names."""
    base = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    files = {"Georgia": "georgia.ttf", "Georgia-Bold": "georgiab.ttf", "Georgia-Italic": "georgiai.ttf"}
    try:
        for name, fn in files.items():
            if name not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(name, str(base / fn)))
        return "Georgia", "Georgia-Bold", "Georgia-Italic"
    except Exception:  # font missing: fall back to the built-in serif
        return "Times-Roman", "Times-Bold", "Times-Italic"


def _qr_image(url: str) -> ImageReader:
    qr = qrcode.QRCode(box_size=8, border=1, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


def draw_letter(c: canvas.Canvas, row: dict, sender: dict = lt.SENDER, when: date | None = None,
                photo: str = "", signature: str = "") -> None:
    reg, bold, ital = _fonts()
    c.setTitle(f"Velarqo letter {row['letter_code']}")
    c.setAuthor(sender["company"])

    # --- Wordmark, top left ---------------------------------------------------
    y = H - TOP
    c.setFillColorRGB(*INK)
    c.setFont(bold, 20)
    c.drawString(LEFT, y - 14, "velarq")
    x_q = LEFT + c.stringWidth("velarq", bold, 20)
    c.setFillColorRGB(*CORAL)
    c.drawString(x_q, y - 14, "o")
    c.setFillColorRGB(*INK)

    # --- Sender block, top right, with photo ----------------------------------
    photo_w, photo_h = 24 * mm, 30 * mm
    px, py = W - RIGHT - photo_w, y - photo_h
    photo = photo or sender.get("photo_path") or ""
    if photo and Path(photo).exists():
        c.drawImage(ImageReader(photo), px, py, photo_w, photo_h, preserveAspectRatio=True, anchor="c")
    else:
        c.setStrokeColorRGB(*GREY)
        c.setDash(2, 2)
        c.rect(px, py, photo_w, photo_h)
        c.setDash()
        c.setFont(reg, 7)
        c.setFillColorRGB(*GREY)
        c.drawCentredString(px + photo_w / 2, py + photo_h / 2 - 2, "{{PHOTO}}")
        c.setFillColorRGB(*INK)
    tx = px - 4 * mm
    c.setFont(bold, 10)
    c.drawRightString(tx, y - 10, sender["name"])
    c.setFont(reg, 9.5)
    for i, line in enumerate([sender["company"], sender["phone"], sender["email"], sender["site"], "", lt.uk_date(when)]):
        c.drawRightString(tx, y - 10 - 13 * (i + 1), line)

    # --- Address block (window zone) ------------------------------------------
    ay = H - 48 * mm
    c.setFont(reg, 10.5)
    addr = [row.get("addressee") or "The Owner", row.get("legal_name") or row["display_name"]]
    addr += [row[k] for k in ("address_1", "address_2", "address_3", "address_4", "address_5") if row.get(k)]
    addr.append(row.get("postcode", ""))
    for i, line in enumerate(addr[:9]):
        c.drawString(LEFT, ay - 13 * i, line)

    # --- Body -----------------------------------------------------------------
    body_top = H - 95 * mm
    qr_h = 24 * mm
    footer_h = 12 * mm
    body_bottom = BOTTOM + footer_h + 2 * mm
    style = ParagraphStyle("body", fontName=reg, fontSize=10.5, leading=14.2, alignment=TA_LEFT,
                           spaceAfter=7.5, textColor="#1a1a1a")
    quote = ParagraphStyle("quote", parent=style, fontName=ital, leftIndent=9 * mm, rightIndent=9 * mm,
                           spaceBefore=1, spaceAfter=9)
    flow = [Paragraph(lt.salutation(row), style)]
    for p in lt.paragraphs(row, sender):
        if p.startswith("> "):
            flow.append(Paragraph(p[2:], quote))
        else:
            flow.append(Paragraph(p, style))
    flow.append(Spacer(1, 2))
    flow.append(Paragraph("Yours sincerely,", style))
    frame = Frame(LEFT, body_bottom, W - LEFT - RIGHT, body_top - body_bottom,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    left = list(flow)
    frame.addFromList(left, c)
    if left:
        raise RuntimeError(f"{row['letter_code']}: letter does not fit on one page ({len(left)} blocks left)")

    # --- Signature + name, placed just under the body's last line -------------
    used_h = sum(f.wrap(W - LEFT - RIGHT, H)[1] + getattr(getattr(f, "style", None), "spaceAfter", 0) for f in flow)
    sy = body_top - used_h - 4 * mm
    sig_h = 12 * mm
    if signature and Path(signature).exists():
        c.drawImage(ImageReader(signature), LEFT, sy - sig_h, 40 * mm, sig_h, preserveAspectRatio=True, anchor="sw", mask="auto")
    c.setFont(bold, 10.5)
    c.drawString(LEFT, sy - sig_h - 4 * mm, sender["name"])
    c.setFont(reg, 10)
    c.drawString(LEFT, sy - sig_h - 4 * mm - 13, sender["company"])

    # --- QR, bottom right -----------------------------------------------------
    qx, qy = W - RIGHT - qr_h, BOTTOM + footer_h
    c.drawImage(_qr_image(row["qr_url"]), qx, qy, qr_h, qr_h)
    c.setFont(reg, 8)
    c.setFillColorRGB(*GREY)
    c.drawRightString(qx - 2 * mm, qy + qr_h / 2 + 4, "How it works, two minutes:")
    c.drawRightString(qx - 2 * mm, qy + qr_h / 2 - 6, sender["site_path"])

    # --- Footer small print ---------------------------------------------------
    c.setFont(reg, 7.2)
    c.setFillColorRGB(*GREY)
    foot = lt.footer(row, sender)
    words, line, lines = foot.split(), "", []
    for w_ in words:
        if c.stringWidth(line + " " + w_, reg, 7.2) > W - LEFT - RIGHT - qr_h - 6 * mm:
            lines.append(line.strip())
            line = w_
        else:
            line += " " + w_
    lines.append(line.strip())
    for i, l in enumerate(lines[:3]):
        c.drawString(LEFT, BOTTOM + 6 * mm - 9 * i, l)
    c.setFillColorRGB(*INK)
    c.showPage()


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40]


SAMPLE_ROW = {
    "letter_code": "L00", "display_name": "Example Windows", "legal_name": "EXAMPLE WINDOWS LIMITED",
    "addressee": "Jane Example", "salutation_first_name": "Jane",
    "address_1": "Unit 4, Sample Trading Estate", "address_2": "Mill Lane", "address_3": "Anytown",
    "address_4": "Yorkshire", "address_5": "", "postcode": "YO1 1AA",
    "incorporation_year": "2009", "years_trading": "17", "website_established_year": "1998",
    "qr_url": "https://velarqo.com/windows?l=L00",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="data/letters_batch1.csv")
    ap.add_argument("--out", default="data/letters/batch1")
    ap.add_argument("--sample", help="write one letter for a fictitious firm to this path and exit")
    ap.add_argument("--photo", default="")
    ap.add_argument("--signature", default="")
    ap.add_argument("--date", help="letter date, YYYY-MM-DD (default today)")
    args = ap.parse_args()
    when = date.fromisoformat(args.date) if args.date else None

    if args.sample:
        Path(args.sample).parent.mkdir(parents=True, exist_ok=True)
        c = canvas.Canvas(args.sample, pagesize=A4)
        draw_letter(c, SAMPLE_ROW, when=when, photo=args.photo, signature=args.signature)
        c.save()
        print(f"wrote {args.sample} ({lt.word_count(SAMPLE_ROW)} body words)")
        return

    rows = list(csv.DictReader(open(args.csv, encoding="utf-8")))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    merged = canvas.Canvas(str(out / "ALL_letters_batch1.pdf"), pagesize=A4)
    for row in rows:
        single = canvas.Canvas(str(out / f"{row['letter_code']}_{_slug(row['display_name'])}.pdf"), pagesize=A4)
        for cv in (single, merged):
            draw_letter(cv, row, when=when, photo=args.photo, signature=args.signature)
        single.save()
    merged.save()
    wc = [lt.word_count(r) for r in rows]
    print(f"wrote {len(rows)} letters to {out} (+ ALL_letters_batch1.pdf); body words {min(wc)}-{max(wc)}")


if __name__ == "__main__":
    main()

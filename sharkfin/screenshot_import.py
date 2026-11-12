"""Read brokerage positions (ticker, shares, average cost) from a screenshot.

Two readers:
* Claude vision, when an Anthropic key is set: reads tables well, including names it has to map to tickers.
* Tesseract OCR (free, runs on the server; installed on Streamlit Cloud through ``packages.txt``): fine on clean
  screenshots, often wrong on busy or dark ones.

Either way the result is only a draft. The Portfolio page shows it in an editable table and nothing is saved until
the user checks it and clicks Add.
"""

from __future__ import annotations

import base64
import io
import json
import re

STOP = {"USD", "ETF", "INC", "LLC", "CORP", "CO", "LTD", "CASH", "TOTAL", "BUY", "SELL", "QTY", "AVG", "COST",
        "PRICE", "VALUE", "SHARES", "SH", "MARKET", "GAIN", "LOSS", "DAY", "TODAY", "ALL", "NAV", "N/A", "NA", "THE",
        "AND", "OF", "PL", "P/L", "YTD", "ACCT", "IRA", "ROTH", "SYMBOL", "NAME", "LAST", "CHANGE", "EQUITY", "A",
        "I", "AM", "PM", "ET", "EST", "EDT", "CLASS", "PLC", "SA", "NV", "AG", "SE", "ADR", "OK", "NEW", "LIMIT",
        "OPEN", "CLOSE", "HIGH", "LOW", "VOL", "MKT", "QUANTITY", "POSITIONS", "HOLDINGS", "RETURN", "PERCENT"}
MAX_PIXELS = 20_000_000  # a phone screenshot is ~4M; anything far bigger is refused before decoding
MAX_SIDE = 12_000
MAX_BYTES = 8_000_000
TICKER = re.compile(r"(?<![A-Za-z$])([A-Z]{1,5}(?:\.[A-Z])?)(?![a-z])")
NUM = re.compile(r"(?<![\w.])(-?\$?\(?-?[\d,]*\.?\d+\)?%?)(?![\w])")


def _to_float(tok: str) -> float | None:
    t = tok.replace("$", "").replace(",", "").replace("(", "-").replace(")", "")
    try:
        return float(t)
    except ValueError:
        return None


def parse_positions(text: str) -> list[dict]:
    """Best-effort rows from OCR text: one row per line that has a ticker and at least one plain number.

    * shares: a number next to 'shares'/'sh'/'qty', else the first plain number (no $ or %)
    * buy_price: a $ number next to 'avg'/'cost', else left empty (the user fills it in or uses today's price)
    """
    rows, seen = [], set()
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]

    def ticker_of(ln):
        return next((m.group(1) for m in TICKER.finditer(ln) if m.group(1) not in STOP), None)

    for i, line in enumerate(lines):
        tick = ticker_of(line)
        if not tick or tick in seen:
            continue
        # phone layouts put "12 shares" on the line under the ticker: read it too, up to the next ticker
        if not re.search(r"\d\s*(?:shares?|shs?|sh\b|units?)|qty|quantity", line.lower()):
            for nxt in lines[i + 1:i + 3]:
                if ticker_of(nxt):
                    break
                line += " " + nxt
        rest = line[line.index(tick) + len(tick):]
        low = rest.lower()
        shares = None
        m = re.search(r"([\d,]*\.?\d+)\s*(?:shares?|shs?|sh\b|units?)", low) or \
            re.search(r"(?:qty|quantity|shares?)[:\s]+([\d,]*\.?\d+)", low)
        if m:
            shares = _to_float(m.group(1))
        nums = [(tok, _to_float(tok)) for tok in NUM.findall(rest)]
        plain = [v for tok, v in nums if v is not None and "$" not in tok and "%" not in tok and v > 0]
        if shares is None and plain:
            shares = plain[0]
        if not shares or shares <= 0:
            continue
        cost = None
        m = re.search(r"(?:avg(?:\.|erage)?(?: cost| price)?|cost(?: basis)?(?: per share)?)[:\s]*\$?\s*([\d,]*\.?\d+)", low)
        if m:
            cost = _to_float(m.group(1))
        rows.append({"symbol": tick, "shares": shares, "buy_price": cost})
        seen.add(tick)
    return rows


def tesseract_available() -> bool:
    try:
        import pytesseract

        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def ocr_text(image_bytes: bytes) -> str:
    """Tesseract text from a screenshot (upscaled and grayscaled; dark-mode screenshots are inverted)."""
    import pytesseract
    from PIL import Image, ImageOps, ImageStat

    img = Image.open(io.BytesIO(image_bytes))  # lazy: only the header is read here
    w, h = img.size
    if w * h > MAX_PIXELS or max(w, h) > MAX_SIDE:
        raise ValueError("image too large")
    img = img.convert("L")
    if ImageStat.Stat(img).mean[0] < 110:  # dark mode
        img = ImageOps.invert(img)
    if w < 1600 and w * h * 4 <= MAX_PIXELS:
        img = img.resize((w * 2, h * 2))
    return pytesseract.image_to_string(img, config="--psm 6")


VISION_PROMPT = """This is a screenshot of a brokerage account. List every stock or ETF position you can see.
Reply with only a JSON array, no prose: [{"symbol": "AAPL", "shares": 10, "buy_price": 182.5}, ...]
- symbol: the US ticker (map a company name to its ticker if only the name is shown)
- shares: the quantity held (a number)
- buy_price: the average cost PER SHARE if shown; if only total cost is shown, divide by shares; else null
Skip cash, totals and anything you can't read. If there are no positions, reply []."""


def claude_positions(image_bytes: bytes, media_type: str = "image/png") -> list[dict]:
    """Positions read by Claude vision (needs ANTHROPIC_API_KEY)."""
    import anthropic

    from . import ai

    if len(image_bytes) > MAX_BYTES:
        raise ValueError("image too large")
    client = anthropic.Anthropic(api_key=ai.api_key())
    msg = client.messages.create(
        model=ai.MODEL, max_tokens=4000,
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": media_type,
                                         "data": base64.b64encode(image_bytes).decode()}},
            {"type": "text", "text": VISION_PROMPT}]}])
    text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    return clean_rows(_json_array(text))


def _json_array(text: str) -> list:
    m = re.search(r"\[.*\]", text or "", re.S)
    try:
        d = json.loads(m.group(0)) if m else []
    except json.JSONDecodeError:
        return []
    return d if isinstance(d, list) else []


def clean_rows(rows: list) -> list[dict]:
    out = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        sym = re.sub(r"[^A-Z.\-]", "", str(r.get("symbol", "")).upper())[:10]
        sh = _to_float(str(r.get("shares", ""))) if r.get("shares") is not None else None
        bp = _to_float(str(r.get("buy_price", ""))) if r.get("buy_price") not in (None, "") else None
        if sym and sh and sh > 0:
            out.append({"symbol": sym, "shares": sh, "buy_price": bp if bp and bp > 0 else None})
    return out

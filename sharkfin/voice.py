"""'Hey SharkFin' voice and typed commands.

Speech is turned into text by the browser's own speech recognition (Chrome, Edge, Safari; free and nothing runs on
the server). Where the browser can't do that (Firefox), the recorder falls back to ``st.audio_input`` and a small
local Whisper model, if ``faster-whisper`` is installed. Text goes through ``parse`` (plain rules, no AI) and becomes a
``Command``; open-ended questions go to the AI analyst when an Anthropic key is set.

Examples: "forecast NVDA for a month", "research Apple", "add 10 shares of Apple at 180", "add Tesla to my
watchlist", "open the playbook", "read me today's market brief".
"""

from __future__ import annotations

import re
from dataclasses import dataclass

PAGES = {  # spoken name -> page file
    "portfolio": "app_pages/portfolio.py", "holdings": "app_pages/portfolio.py",
    "watchlist": "app_pages/portfolio.py",
    "dashboard": "app_pages/home.py", "market dashboard": "app_pages/home.py", "home": "app_pages/home.py",
    "market": "app_pages/home.py",
    "top performers": "app_pages/scanner.py", "scanner": "app_pages/scanner.py", "signals": "app_pages/scanner.py",
    "news": "app_pages/news.py", "headlines": "app_pages/news.py",
    "research": "app_pages/research.py", "valuation": "app_pages/research.py",
    "forecasts": "app_pages/predictions.py", "forecast": "app_pages/predictions.py",
    "predictions": "app_pages/predictions.py",
    "playbook": "app_pages/playbook.py", "strategy playbook": "app_pages/playbook.py",
    "strategy lab": "app_pages/strategy_lab.py", "lab": "app_pages/strategy_lab.py",
    "speculation": "app_pages/speculation.py", "speculation radar": "app_pages/speculation.py",
    "radar": "app_pages/speculation.py",
}
HORIZON_WORDS = {"week": "1 week", "month": "1 month", "quarter": "3 months", "three months": "3 months",
                 "3 months": "3 months", "six months": "6 months", "6 months": "6 months", "half a year": "6 months",
                 "year": "1 year", "twelve months": "1 year", "12 months": "1 year"}
NUMBERS = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
           "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "fifteen": 15, "twenty": 20, "twenty five": 25,
           "thirty": 30, "forty": 40, "fifty": 50, "hundred": 100, "a hundred": 100, "one hundred": 100}
_NUM = r"(\d+(?:[.,]\d+)?|" + "|".join(sorted((re.escape(k) for k in NUMBERS), key=len, reverse=True)) + r")"
_FILLER = r"(?:hey |ok |okay )?(?:shark ?fin[,.!]? )?(?:please |can you |could you |would you |i want to |let's )*"


@dataclass
class Command:
    action: str  # page | forecast | research | add | watch | brief | ask | empty
    page: str | None = None
    query: str = ""  # company name or ticker as spoken
    shares: float | None = None
    price: float | None = None
    horizon: str | None = None
    text: str = ""

    def describe(self) -> str:
        if self.action == "forecast":
            return f"Forecast {self.query.upper()} over {self.horizon or '3 months'}"
        if self.action == "research":
            return f"Research {self.query.upper()}"
        if self.action == "add":
            at = f" at ${self.price:,.2f}" if self.price else " at today's price"
            return f"Add {self.shares:g} shares of {self.query.upper()}{at}"
        if self.action == "watch":
            return f"Add {self.query.upper()} to the watchlist"
        if self.action == "page":
            name = next((k for k, v in PAGES.items() if v == self.page), self.page)
            return f"Open {name.title()}"
        if self.action == "brief":
            return "Read today's market brief"
        if self.action == "ask":
            return f"Ask the AI analyst: “{self.text}”"
        return "Nothing to do"


def _num(s: str | None) -> float | None:
    if not s:
        return None
    s = s.strip().lower()
    if s in NUMBERS:
        return float(NUMBERS[s])
    try:
        return float(s.replace(",", ""))
    except ValueError:
        return None


def _clean(name: str) -> str:
    name = re.sub(r"^(the |shares of |stock |of )+", "", name.strip(" .,!?"))
    name = re.sub(r"( stock| shares| please| for me)+$", "", name)
    return name.strip(" .,!?")


def parse(text: str) -> Command:
    raw = (text or "").strip()
    t = re.sub(r"\s+", " ", raw.lower()).strip(" .!?")
    t = re.sub(r"\$", "", t)
    t = re.sub("^" + _FILLER, "", t).strip()
    if not t:
        return Command("empty", text=raw)

    if re.search(r"\b(brief|briefing|summary of (the )?market|how('s| is) the market)\b", t):
        return Command("brief", text=raw)

    m = re.match(r"(?:add|put) (.+?) (?:to|on|in) (?:my |the )?watch ?list$", t) or \
        re.match(r"watch (.+)$", t)
    if m:
        return Command("watch", query=_clean(m.group(1)), text=raw)

    m = re.match(r"(?:add|buy|bought|record|log) " + _NUM + r" (?:shares?|stocks?|units?) (?:of )?(.+?)"
                 r"(?: (?:at|for|@)(?: a price of)? " + _NUM + r"(?: dollars| bucks| each| a share| per share)*)?$", t)
    if m:
        return Command("add", query=_clean(m.group(2)), shares=_num(m.group(1)), price=_num(m.group(3)), text=raw)

    m = re.match(r"(?:forecast|predict|projection for|prediction for|outlook for|where will) (.+?)"
                 r"(?: (?:be|go|trade))?(?: (?:for|over|in|after) (?:the next |a |one |next )?(.+))?$", t)
    if m:
        hz = None
        if m.group(2):
            hz = next((v for k, v in sorted(HORIZON_WORDS.items(), key=lambda kv: -len(kv[0])) if k in m.group(2)), None)
        return Command("forecast", query=_clean(m.group(1)), horizon=hz, text=raw)

    m = re.match(r"(?:open|show|go to|take me to|switch to|navigate to)(?: me)?(?: my| the)? (.+?)(?: page| tab)?$", t)
    if m and _clean(m.group(1)) in PAGES:
        return Command("page", page=PAGES[_clean(m.group(1))], text=raw)
    if t in PAGES:
        return Command("page", page=PAGES[t], text=raw)

    m = re.match(r"(?:research|analy[sz]e|value|valuation (?:of|for)|look up|tell me about|what's the fair value of"
                 r"|what is the fair value of) (.+)$", t)
    if m:
        return Command("research", query=_clean(m.group(1)), text=raw)

    return Command("ask", text=raw)


# ---------------------------------------------------------------------------
# Browser speech (Streamlit components v2: inline JS, value sent back to Python)
# ---------------------------------------------------------------------------

MIC_HTML = """<div class="sfv"><button type="button" class="mic" aria-label="Speak a command">
<span class="dot"></span><span class="lbl">Tap to speak</span></button><div class="hint"></div></div>"""

MIC_CSS = """
.sfv {font-family: var(--st-font, inherit);}
.mic {display:flex; align-items:center; gap:.55rem; width:100%; padding:.5rem .8rem; border-radius:.55rem;
  border:1px solid var(--st-border-color, rgba(128,128,128,.35)); background: transparent; color: var(--st-text-color);
  font: inherit; font-size:.9rem; cursor:pointer; transition: border-color .2s, background-color .2s;}
.mic:hover {border-color: var(--st-primary-color);}
.mic .dot {width:.6rem; height:.6rem; border-radius:50%; background: var(--st-primary-color); flex:none;}
.mic.on {border-color: var(--st-primary-color); background: color-mix(in srgb, var(--st-primary-color) 12%, transparent);}
.mic.on .dot {animation: sfpulse 1s ease-in-out infinite;}
@keyframes sfpulse {0%,100% {opacity:1; transform:scale(1)} 50% {opacity:.35; transform:scale(.7)}}
.hint {font-size:.76rem; opacity:.7; margin-top:.3rem; min-height:1em;}
@media (prefers-reduced-motion: reduce) {.mic.on .dot {animation:none}}
"""

MIC_JS = """
export default function(component) {
  const { parentElement, setTriggerValue, setStateValue } = component;
  const btn = parentElement.querySelector('.mic');
  const lbl = parentElement.querySelector('.lbl');
  const hint = parentElement.querySelector('.hint');
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {
    setStateValue('supported', false);
    btn.disabled = true; btn.style.opacity = .55; btn.style.cursor = 'not-allowed';
    hint.textContent = 'Voice needs Chrome, Edge or Safari. You can type below.';
    return;
  }
  setStateValue('supported', true);
  let rec = null;
  const stop = () => { btn.classList.remove("on"); lbl.textContent = "Tap to speak"; };
  btn.onclick = () => {
    if (rec) { rec.stop(); return; }
    rec = new SR();
    rec.lang = 'en-US'; rec.interimResults = true; rec.maxAlternatives = 1;
    btn.classList.add('on'); lbl.textContent = 'Listening… tap to stop'; hint.textContent = '';
    let finalText = '';
    rec.onresult = (e) => {
      let interim = '';
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const r = e.results[i];
        if (r.isFinal) finalText += r[0].transcript; else interim += r[0].transcript;
      }
      hint.textContent = (finalText + ' ' + interim).trim();
    };
    rec.onerror = (e) => {
      hint.textContent = e.error === 'not-allowed' ? 'Allow the microphone for this site to use voice.' :
        e.error === 'no-speech' ? "Didn't catch that. Tap and try again." : 'Voice error: ' + e.error;
    };
    rec.onend = () => {
      stop(); rec = null;
      const t = finalText.trim();
      if (t) setTriggerValue('heard', t);
    };
    rec.start();
  };
}
"""

SPEAK_JS = """
export default function(component) {
  const { parentElement, data } = component;
  const btn = parentElement.querySelector('button');
  if (!('speechSynthesis' in window)) { btn.disabled = true; btn.title = 'Your browser cannot read aloud'; return; }
  btn.onclick = () => {
    if (speechSynthesis.speaking) { speechSynthesis.cancel(); btn.textContent = btn.dataset.label; return; }
    const u = new SpeechSynthesisUtterance(data || '');
    u.rate = 1.02; u.lang = 'en-US';
    u.onend = () => { btn.textContent = btn.dataset.label; };
    btn.textContent = 'Stop reading';
    speechSynthesis.speak(u);
  };
}
"""

_components: dict = {}


def _component(name: str, **kw):
    if name not in _components:
        import streamlit as st

        _components[name] = st.components.v2.component(name, **kw)
    return _components[name]


def mic(key: str = "sf_mic"):
    """The 'Hey SharkFin' button. Returns (heard_text_or_None, browser_supports_speech)."""
    comp = _component("sharkfin_mic", html=MIC_HTML, css=MIC_CSS, js=MIC_JS)
    res = comp(key=key, on_heard_change=lambda: None, on_supported_change=lambda: None)
    return getattr(res, "heard", None), getattr(res, "supported", None)


def speak_button(text: str, label: str = "Read it aloud", key: str = "sf_speak"):
    """A button that reads ``text`` with the browser's built-in voice."""
    import html as _h

    comp = _component("sharkfin_speak", html=f"<button type='button' class='sp' data-label='{_h.escape(label)}'>"
                                             f"{_h.escape(label)}</button>",
                      css=MIC_CSS.replace(".mic", ".sp"), js=SPEAK_JS)
    comp(key=key, data=text)


# ---------------------------------------------------------------------------
# Server-side speech to text (fallback, only if faster-whisper is installed)
# ---------------------------------------------------------------------------


def whisper_available() -> bool:
    try:
        import faster_whisper  # noqa: F401
    except Exception:
        return False
    return True


def transcribe(audio_bytes: bytes) -> str:
    """Speech to text with Whisper tiny.en (int8, about 75 MB). Loaded once per server, on first use."""
    import io

    import streamlit as st

    @st.cache_resource(show_spinner="Loading the speech model (first time only)…")
    def _model():
        from faster_whisper import WhisperModel

        return WhisperModel("tiny.en", device="cpu", compute_type="int8", cpu_threads=2)

    segs, _ = _model().transcribe(io.BytesIO(audio_bytes), beam_size=1, language="en", vad_filter=True)
    return " ".join(s.text.strip() for s in segs).strip()


# ---------------------------------------------------------------------------
# Market brief
# ---------------------------------------------------------------------------


def brief_text(portfolio: list | None = None) -> str:
    """A short spoken summary of the market's last session (and the portfolio's day, if there is one)."""
    import numpy as np
    import pandas as pd

    from . import data

    def last2(sym):
        h = data.history(sym, "1y")
        c = h["Close"].dropna() if not h.empty else pd.Series(dtype=float)
        return c

    parts = []
    spy, qqq, vix = last2("SPY"), last2("QQQ"), last2("^VIX")
    for name, c in (("The S&P 500", spy), ("The Nasdaq 100", qqq)):
        if len(c) > 1:
            ch = c.iloc[-1] / c.iloc[-2] - 1
            parts.append(f"{name} {'rose' if ch >= 0 else 'fell'} {abs(ch):.1%}")
    if len(vix):
        v = float(vix.iloc[-1])
        mood = "calm" if v < 16 else "normal" if v < 22 else "nervous" if v < 30 else "fearful"
        parts.append(f"the VIX is at {v:.0f}, which is {mood}")
    text = (", ".join(parts) + ".") if parts else "Market data isn't available right now."
    if len(spy) > 200:
        gap = spy.iloc[-1] / spy.iloc[-200:].mean() - 1
        text += (f" The S&P is {abs(gap):.0%} {'above' if gap >= 0 else 'below'} its 200-day average, so the long-term "
                 f"trend is {'up' if gap >= 0 else 'down'}.")
    if portfolio:
        try:
            lots = pd.DataFrame(portfolio)
            sh = lots.groupby(lots["symbol"].astype(str).str.upper())["shares"].sum().astype(float)
            px = data.download_prices(tuple(sh.index), period="5d").ffill()
            if len(px) > 1:
                v1, v0 = (px.iloc[-1] * sh).sum(), (px.iloc[-2] * sh).sum()
                if v0 > 0 and np.isfinite(v1 / v0):
                    ch = v1 / v0 - 1
                    text += f" Your portfolio {'gained' if ch >= 0 else 'lost'} {abs(ch):.1%} on the day."
        except Exception:
            pass
    return text.replace("S&P", "S and P")

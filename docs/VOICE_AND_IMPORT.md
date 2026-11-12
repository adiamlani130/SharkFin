# Voice commands and screenshot import

## "Hey SharkFin" (sidebar, every page)

Tap **Tap to speak** and say a command, or type it in the box underneath.

| Say | What happens |
| --- | --- |
| "forecast NVDA for a month" | Opens Forecasts on NVDA, 1-month view (week / month / 3 or 6 months / year) |
| "research Apple", "what's the fair value of Microsoft" | Opens Research & Valuation on that stock |
| "add 10 shares of Apple at 180" | Adds the position (leave out the price to use today's) |
| "add Tesla to my watchlist" | Adds it to the watchlist |
| "open the playbook", "show my portfolio", "top performers" | Switches page |
| "read me today's market brief" | Writes a short brief (S&P 500, Nasdaq 100, VIX, the 200-day trend, your portfolio's day); **Read it aloud** speaks it |
| anything else | Goes to the AI analyst if `ANTHROPIC_API_KEY` is set |

How it works: the browser's built-in speech recognition turns speech into text (Chrome, Edge and Safari,
including iPhone). It's free, and nothing runs on SharkFin's server. Plain rules in `sharkfin/voice.py`, not AI,
turn the text into a command. Firefox has no speech recognition: there, typing works, and recording works too if
`faster-whisper` is added to requirements (Whisper tiny.en, about 75 MB, loaded on first use). It's left out by
default because Streamlit Cloud's memory is tight. Read-aloud uses the browser's own voice.

## Import from a screenshot (Portfolio)

Upload or snap your broker's positions screen and click **Read screenshot**. The tickers, shares and costs it finds
go into an editable table. Nothing is added until you click **Add these positions**, and an empty cost uses today's
price.

- With `ANTHROPIC_API_KEY` set, Claude reads the image. It handles busy tables and company names well, and each
  read uses a few cents of credits.
- Otherwise the free Tesseract OCR engine reads it. `packages.txt` installs it on Streamlit Cloud, and
  `pytesseract` comes from requirements. It reads clean light or dark phone screenshots well, but often
  misses or misreads numbers on dense desktop tables. Always check the preview.

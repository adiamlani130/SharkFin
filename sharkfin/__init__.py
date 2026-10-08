"""SharkFin analytics core.

Pure, testable analytics (no Streamlit imports) used by the UI pages:

- ``indicators``  vectorised technical indicators (Wilder smoothing, ADX, ATR ...)
- ``risk``        performance and tail-risk statistics
- ``forecasting`` walk-forward validated, probabilistic ensemble forecasts
- ``valuation``   DCF, reverse DCF, peer multiples, quality / distress scores
- ``factors``     cross-sectional multi-factor stock ranking + backtest
- ``portfolio``   HRP, min-variance and max-Sharpe optimisation
- ``backtest``    rule-based strategy backtester with trading costs
- ``sentiment``   finance-lexicon news sentiment and BM25 relevance ranking
- ``data``        market-data access layer (yfinance) with caching
- ``ai``          optional Claude-written analyst report
"""

import time

__version__ = "2.0.0"
LOADED_AT = time.time()  # main.py reloads the package when a deploy changes its files after this

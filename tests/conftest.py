import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def make_ohlcv(n=900, drift=0.0004, vol=0.012, seed=0, start=100.0):
    rng = np.random.default_rng(seed)
    r = rng.standard_t(5, n) * vol * np.sqrt(3 / 5) + drift
    close = start * np.exp(np.cumsum(r))
    idx = pd.bdate_range("2022-01-03", periods=n)
    high = close * (1 + np.abs(rng.normal(0, 0.006, n)))
    low = close * (1 - np.abs(rng.normal(0, 0.006, n)))
    return pd.DataFrame({"Open": close, "High": high, "Low": low, "Close": close,
                         "Volume": rng.integers(1_000_000, 3_000_000, n).astype(float)}, index=idx)


@pytest.fixture
def ohlcv():
    return make_ohlcv()


@pytest.fixture
def price_panel():
    """40 synthetic stocks with a planted momentum effect."""
    rng = np.random.default_rng(42)
    n, k = 700, 40
    idx = pd.bdate_range("2022-01-03", periods=n)
    mkt = rng.normal(0.0003, 0.01, n)
    drifts = np.linspace(-0.0006, 0.0012, k)
    rets = mkt[:, None] * rng.uniform(0.6, 1.4, k) + drifts + rng.normal(0, 0.012, (n, k))
    return pd.DataFrame(100 * np.exp(np.cumsum(rets, axis=0)), index=idx, columns=[f"S{i:02d}" for i in range(k)])

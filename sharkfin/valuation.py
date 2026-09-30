"""Intrinsic and relative valuation, plus accounting quality / distress scores.

All functions operate on plain numbers or pandas objects so they are testable
without network access. ``Financials`` normalises yfinance statement frames
(rows = line items, columns = fiscal period end dates, newest first).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import optimize

# Damodaran-style implied US equity risk premium; overridable in the UI.
DEFAULT_ERP = 0.045
DEFAULT_TAX = 0.21


# ---------------------------------------------------------------------------
# Statement normalisation
# ---------------------------------------------------------------------------


def _line(df: pd.DataFrame | None, *names: str) -> pd.Series:
    """First matching statement line as a Series (newest first), else empty."""
    if df is None or df.empty:
        return pd.Series(dtype=float)
    for n in names:
        if n in df.index:
            s = pd.to_numeric(df.loc[n], errors="coerce")
            if isinstance(s, pd.DataFrame):
                s = s.iloc[0]
            return s
    return pd.Series(dtype=float)


def _v(s: pd.Series, i: int = 0, default=np.nan) -> float:
    s = s.dropna() if s is not None else s
    if s is None or len(s) <= i:
        return default
    return float(s.iloc[i])


@dataclass
class Financials:
    income: pd.DataFrame | None = None
    balance: pd.DataFrame | None = None
    cashflow: pd.DataFrame | None = None

    def revenue(self): return _line(self.income, "Total Revenue", "Operating Revenue")
    def gross_profit(self): return _line(self.income, "Gross Profit")
    def ebit(self): return _line(self.income, "EBIT", "Operating Income")
    def ebitda(self): return _line(self.income, "EBITDA", "Normalized EBITDA")
    def net_income(self): return _line(self.income, "Net Income", "Net Income Common Stockholders")
    def interest_expense(self): return _line(self.income, "Interest Expense", "Interest Expense Non Operating").abs()
    def pretax_income(self): return _line(self.income, "Pretax Income")
    def tax(self): return _line(self.income, "Tax Provision")
    def total_assets(self): return _line(self.balance, "Total Assets")
    def total_liabilities(self): return _line(self.balance, "Total Liabilities Net Minority Interest", "Total Liabilities")
    def current_assets(self): return _line(self.balance, "Current Assets")
    def current_liabilities(self): return _line(self.balance, "Current Liabilities")
    def long_term_debt(self): return _line(self.balance, "Long Term Debt", "Long Term Debt And Capital Lease Obligation")
    def total_debt(self): return _line(self.balance, "Total Debt")
    def cash(self): return _line(self.balance, "Cash Cash Equivalents And Short Term Investments", "Cash And Cash Equivalents")
    def equity(self): return _line(self.balance, "Stockholders Equity", "Common Stock Equity")
    def retained_earnings(self): return _line(self.balance, "Retained Earnings")
    def shares(self): return _line(self.balance, "Ordinary Shares Number", "Share Issued")
    def cfo(self): return _line(self.cashflow, "Operating Cash Flow", "Cash Flow From Continuing Operating Activities")
    def capex(self): return _line(self.cashflow, "Capital Expenditure").abs()
    def sbc(self): return _line(self.cashflow, "Stock Based Compensation")

    def fcf(self) -> pd.Series:
        f = _line(self.cashflow, "Free Cash Flow")
        if f.dropna().empty:
            f = self.cfo() - self.capex()
        return f

    def effective_tax_rate(self) -> float:
        t, p = self.tax(), self.pretax_income()
        rates = (t / p).replace([np.inf, -np.inf], np.nan).dropna()
        rates = rates[(rates > 0) & (rates < 0.5)]
        return float(rates.iloc[:3].mean()) if len(rates) else DEFAULT_TAX

    def revenue_cagr(self, years: int = 3) -> float:
        r = self.revenue().dropna()
        if len(r) < 2:
            return np.nan
        n = min(years, len(r) - 1)
        if r.iloc[n] <= 0 or r.iloc[0] <= 0:
            return np.nan
        return float((r.iloc[0] / r.iloc[n]) ** (1 / n) - 1)


# ---------------------------------------------------------------------------
# Cost of capital
# ---------------------------------------------------------------------------


@dataclass
class WACCResult:
    wacc: float
    cost_of_equity: float
    cost_of_debt_after_tax: float
    weight_equity: float
    weight_debt: float
    beta: float
    rf: float
    erp: float
    tax_rate: float


def wacc(market_cap: float, total_debt: float, beta: float, rf: float, erp: float = DEFAULT_ERP,
         interest_expense: float = np.nan, tax_rate: float = DEFAULT_TAX) -> WACCResult:
    """CAPM cost of equity + synthetic/implied cost of debt, market-value weights."""
    beta = float(np.clip(beta if np.isfinite(beta) else 1.0, 0.3, 3.0))
    ke = rf + beta * erp
    debt = max(float(total_debt or 0), 0.0)
    if debt > 0 and np.isfinite(interest_expense) and interest_expense > 0:
        kd = np.clip(interest_expense / debt, rf, rf + 0.08)
    else:
        kd = rf + 0.015
    t = float(np.clip(tax_rate if np.isfinite(tax_rate) else DEFAULT_TAX, 0, 0.35))
    E, D = max(float(market_cap or 0), 1.0), debt
    we, wd = E / (E + D), D / (E + D)
    w = we * ke + wd * kd * (1 - t)
    return WACCResult(float(w), float(ke), float(kd * (1 - t)), float(we), float(wd), beta, rf, erp, t)


# ---------------------------------------------------------------------------
# Discounted cash flow
# ---------------------------------------------------------------------------


@dataclass
class DCFResult:
    value_per_share: float
    enterprise_value: float
    equity_value: float
    pv_explicit: float
    pv_terminal: float
    terminal_share: float
    fcf_path: np.ndarray
    growth_path: np.ndarray
    discount_factors: np.ndarray
    implied_exit_multiple: float  # TV / final-year FCF


def dcf(fcf0: float, growth: float, wacc_: float, terminal_growth: float, net_debt: float,
        shares: float, high_growth_years: int = 5, fade_years: int = 5) -> DCFResult:
    """Three-stage FCFF DCF.

    Stage 1: ``growth`` for ``high_growth_years``; stage 2: linear fade to
    ``terminal_growth`` over ``fade_years``; stage 3: Gordon growth terminal
    value. Uses the mid-year discounting convention.
    """
    if wacc_ <= terminal_growth:
        raise ValueError("WACC must exceed terminal growth.")
    if shares <= 0:
        raise ValueError("Share count must be positive.")
    n = high_growth_years + fade_years
    g = np.empty(n)
    g[:high_growth_years] = growth
    if fade_years:
        g[high_growth_years:] = np.linspace(growth, terminal_growth, fade_years + 2)[1:-1]
    fcf = fcf0 * np.cumprod(1 + g)
    t = np.arange(1, n + 1) - 0.5
    df = (1 + wacc_) ** -t
    pv_explicit = float((fcf * df).sum())
    tv = fcf[-1] * (1 + terminal_growth) / (wacc_ - terminal_growth)
    # Mid-year convention applies to the terminal cash flows too.
    pv_tv = float(tv * (1 + wacc_) ** -(n - 0.5))
    ev = pv_explicit + pv_tv
    eq = ev - net_debt
    return DCFResult(
        value_per_share=float(eq / shares), enterprise_value=float(ev), equity_value=float(eq),
        pv_explicit=pv_explicit, pv_terminal=pv_tv, terminal_share=pv_tv / ev if ev else np.nan,
        fcf_path=fcf, growth_path=g, discount_factors=df,
        implied_exit_multiple=float(tv / fcf[-1]) if fcf[-1] else np.nan,
    )


def sensitivity_grid(fcf0, growth, wacc_, terminal_growth, net_debt, shares,
                     wacc_steps=(-0.02, -0.01, 0, 0.01, 0.02), tg_steps=(-0.01, -0.005, 0, 0.005, 0.01)) -> pd.DataFrame:
    rows = {}
    for dw in wacc_steps:
        row = {}
        for dg in tg_steps:
            w, tg = wacc_ + dw, terminal_growth + dg
            try:
                row[f"{tg:.1%}"] = dcf(fcf0, growth, w, tg, net_debt, shares).value_per_share
            except ValueError:
                row[f"{tg:.1%}"] = np.nan
        rows[f"{w:.1%}"] = row
    df = pd.DataFrame(rows).T
    df.index.name = "WACC \\ terminal g"
    return df


def reverse_dcf(price: float, fcf0: float, wacc_: float, terminal_growth: float, net_debt: float,
                shares: float) -> float:
    """Stage-1 growth rate the market price implies (market-implied expectations)."""
    if fcf0 <= 0:
        return np.nan

    def f(g):
        return dcf(fcf0, g, wacc_, terminal_growth, net_debt, shares).value_per_share - price

    try:
        lo, hi = -0.5, 1.5
        if f(lo) * f(hi) > 0:
            return np.nan
        return float(optimize.brentq(f, lo, hi, xtol=1e-6))
    except Exception:
        return np.nan


def monte_carlo_dcf(fcf0, growth, wacc_, terminal_growth, net_debt, shares, n: int = 5000,
                    growth_sd: float = 0.04, wacc_sd: float = 0.01, tg_sd: float = 0.005,
                    fcf_sd: float = 0.10, seed: int = 3) -> np.ndarray:
    """Distribution of per-share value under parameter uncertainty (vectorised)."""
    rng = np.random.default_rng(seed)
    g = rng.normal(growth, growth_sd, n)
    w = rng.normal(wacc_, wacc_sd, n)
    tg = np.minimum(rng.normal(terminal_growth, tg_sd, n), w - 0.01)
    f0 = fcf0 * np.exp(rng.normal(0, fcf_sd, n))
    hg, fade = 5, 5
    years = hg + fade
    gpath = np.empty((n, years))
    gpath[:, :hg] = g[:, None]
    fracs = np.arange(1, fade + 1) / (fade + 1)
    gpath[:, hg:] = g[:, None] * (1 - fracs) + tg[:, None] * fracs
    fcf = f0[:, None] * np.cumprod(1 + gpath, axis=1)
    t = np.arange(1, years + 1) - 0.5
    pv = (fcf * (1 + w[:, None]) ** -t).sum(axis=1)
    tv = fcf[:, -1] * (1 + tg) / (w - tg) * (1 + w) ** -(years - 0.5)
    return (pv + tv - net_debt) / shares


def normalized_fcf(fin: Financials, ttm_fcf: float = np.nan, subtract_sbc: bool = False) -> float:
    """Normalised starting FCF: blend of TTM and 3-year average, optionally net of SBC."""
    hist = fin.fcf().dropna().iloc[:3]
    parts = [v for v in [ttm_fcf, hist.mean() if len(hist) else np.nan] if np.isfinite(v)]
    base = float(np.mean(parts)) if parts else np.nan
    if subtract_sbc:
        sbc = _v(fin.sbc(), 0, 0.0)
        base -= sbc if np.isfinite(sbc) else 0.0
    return base


def forward_growth(growth_estimates) -> float:
    """Consensus next-fiscal-year growth (``+1y`` row of Yahoo's growth
    estimates), falling back to long-term growth; NaN when unavailable."""
    if not isinstance(growth_estimates, pd.DataFrame) or growth_estimates.empty:
        return np.nan
    col = "stockTrend" if "stockTrend" in growth_estimates.columns else growth_estimates.columns[0]
    for row in ("+1y", "LTG"):
        if row in growth_estimates.index:
            v = pd.to_numeric(pd.Series([growth_estimates.at[row, col]]), errors="coerce").iloc[0]
            if np.isfinite(v):
                return float(v)
    return np.nan


def default_growth(fin: Financials, *estimates: float) -> float:
    """Median of the given growth estimates and the 3-year revenue CAGR,
    clipped to a sane range. The median keeps one extreme input (a cyclical's
    commodity-driven revenue jump, a one-off bad year) from setting the DCF."""
    parts = [x for x in (*estimates, fin.revenue_cagr(3)) if x is not None and np.isfinite(x)]
    g = float(np.median(parts)) if parts else 0.05
    return float(np.clip(g, -0.05, 0.30))


# ---------------------------------------------------------------------------
# Relative valuation (peer multiples)
# ---------------------------------------------------------------------------

MULTIPLES = {
    # multiple: (target metric key, is_enterprise_multiple)
    "P/E (fwd)": ("forward_eps", False),
    "P/E (ttm)": ("trailing_eps", False),
    "EV/EBITDA": ("ebitda", True),
    "EV/Sales": ("revenue", True),
    "P/FCF": ("fcf_per_share", False),
    "P/B": ("book_per_share", False),
}


def implied_prices(target: dict, peers: pd.DataFrame) -> pd.DataFrame:
    """Implied share price from peer median/25th/75th percentile multiples.

    ``target`` needs keys: price, shares, net_debt and the metric keys in
    MULTIPLES. ``peers`` has one row per peer and a column per multiple name.
    """
    rows = []
    shares, net_debt = target.get("shares", np.nan), target.get("net_debt", 0.0) or 0.0
    for mult, (metric, is_ev) in MULTIPLES.items():
        if mult not in peers.columns:
            continue
        m = pd.to_numeric(peers[mult], errors="coerce")
        m = m[m > 0].dropna()
        if len(m) > 4:  # drop extreme outliers (e.g. P/E of 900 on depressed earnings)
            q1, q3 = m.quantile(0.25), m.quantile(0.75)
            m = m[m <= q3 + 3 * (q3 - q1)]
        base = target.get(metric, np.nan)
        if m.notna().sum() < 2 or not np.isfinite(base) or base <= 0:
            continue
        out = {"Multiple": mult, "Peers": int(m.notna().sum()), "Target": target.get(mult, np.nan)}
        for lbl, q in (("Low (25th)", 0.25), ("Median", 0.5), ("High (75th)", 0.75)):
            mq = float(m.quantile(q))
            if is_ev:
                price = (mq * base - net_debt) / shares if shares else np.nan
            else:
                price = mq * base
            out[lbl] = price
        out["Peer median multiple"] = float(m.median())
        rows.append(out)
    df = pd.DataFrame(rows)
    if not df.empty and target.get("price"):
        df["Upside (median)"] = df["Median"] / target["price"] - 1
    return df


def regression_multiple(peers: pd.DataFrame, target: dict, y: str = "EV/Sales",
                        xs=("revenue_growth", "ebitda_margin")) -> dict:
    """Fundamentals-adjusted multiple: cross-sectional OLS of log(multiple) on
    growth and margins across peers, evaluated at the target's fundamentals."""
    cols = [y, *xs]
    if not set(cols).issubset(peers.columns):
        return {}
    d = peers[cols].apply(pd.to_numeric, errors="coerce").dropna()
    d = d[d[y] > 0]
    if len(d) < 6 or any(not np.isfinite(target.get(x, np.nan)) for x in xs):
        return {}
    X = np.column_stack([np.ones(len(d)), *[d[x].clip(-0.5, 1.0) for x in xs]])
    beta, *_ = np.linalg.lstsq(X, np.log(d[y]), rcond=None)
    resid = np.log(d[y]) - X @ beta
    r2 = 1 - resid.var() / np.log(d[y]).var() if np.log(d[y]).var() > 0 else np.nan
    xt = np.array([1.0, *[np.clip(target[x], -0.5, 1.0) for x in xs]])
    fitted = float(np.exp(xt @ beta))
    return {"multiple": y, "fitted": fitted, "r2": float(r2), "n": len(d), "coefs": dict(zip(["const", *xs], beta))}


# ---------------------------------------------------------------------------
# Quality and distress scores
# ---------------------------------------------------------------------------


@dataclass
class ScoreResult:
    score: float
    max_score: float
    label: str
    components: list = field(default_factory=list)  # (name, value/passed, detail)


def piotroski_f_score(fin: Financials) -> ScoreResult | None:
    """Piotroski (2000) 9-point F-score from two consecutive fiscal years."""
    ni, cfo, ta = fin.net_income(), fin.cfo(), fin.total_assets()
    if len(ta.dropna()) < 3 or len(ni.dropna()) < 2:
        return None
    ta0, ta1, ta2 = _v(ta, 0), _v(ta, 1), _v(ta, 2)
    roa0, roa1 = _v(ni, 0) / ((ta0 + ta1) / 2), _v(ni, 1) / ((ta1 + ta2) / 2)
    cfo0 = _v(cfo, 0)
    ltd = fin.long_term_debt()
    lev0, lev1 = _v(ltd, 0, 0) / ta0, _v(ltd, 1, 0) / ta1
    ca, cl = fin.current_assets(), fin.current_liabilities()
    cr0, cr1 = _v(ca, 0) / _v(cl, 0), _v(ca, 1) / _v(cl, 1)
    sh = fin.shares()
    rev, gp = fin.revenue(), fin.gross_profit()
    gm0, gm1 = _v(gp, 0) / _v(rev, 0), _v(gp, 1) / _v(rev, 1)
    at0, at1 = _v(rev, 0) / ta1, _v(rev, 1) / ta2

    tests = [
        ("Positive ROA", roa0 > 0, f"ROA {roa0:.1%}"),
        ("Positive operating cash flow", cfo0 > 0, f"CFO {cfo0/1e9:.2f}B"),
        ("Improving ROA", roa0 > roa1, f"{roa1:.1%} → {roa0:.1%}"),
        ("Cash earnings > accounting earnings (accruals)", cfo0 / ta0 > roa0, f"CFO/TA {cfo0/ta0:.1%}"),
        ("Falling leverage", lev0 <= lev1, f"LTD/TA {lev1:.1%} → {lev0:.1%}"),
        ("Improving liquidity", cr0 > cr1, f"Current ratio {cr1:.2f} → {cr0:.2f}"),
        ("No dilution", _v(sh, 0, 0) <= _v(sh, 1, 0) * 1.005 if len(sh.dropna()) > 1 else True, "Share count"),
        ("Improving gross margin", gm0 > gm1, f"{gm1:.1%} → {gm0:.1%}"),
        ("Improving asset turnover", at0 > at1, f"{at1:.2f} → {at0:.2f}"),
    ]
    tests = [(n, bool(p) if np.isfinite(float(p)) else False, d) for n, p, d in tests]
    s = sum(p for _, p, _ in tests)
    label = "Strong" if s >= 7 else "Average" if s >= 4 else "Weak"
    return ScoreResult(s, 9, label, tests)


def altman_z(fin: Financials, market_cap: float) -> ScoreResult | None:
    """Altman Z-score (original public-company model)."""
    ta = _v(fin.total_assets())
    if not np.isfinite(ta) or ta <= 0:
        return None
    wc = _v(fin.current_assets()) - _v(fin.current_liabilities())
    re = _v(fin.retained_earnings(), 0, 0.0)
    ebit = _v(fin.ebit())
    tl = _v(fin.total_liabilities())
    sales = _v(fin.revenue())
    parts = [
        ("Working capital / assets", 1.2, wc / ta),
        ("Retained earnings / assets", 1.4, re / ta),
        ("EBIT / assets", 3.3, ebit / ta),
        ("Market cap / liabilities", 0.6, market_cap / tl if tl else np.nan),
        ("Sales / assets", 1.0, sales / ta),
    ]
    z = sum(w * x for _, w, x in parts if np.isfinite(x))
    label = "Safe" if z > 2.99 else "Grey zone" if z > 1.81 else "Distress"
    return ScoreResult(float(z), np.nan, label, [(n, x, f"weight {w}") for n, w, x in parts])


def quality_metrics(fin: Financials, market_cap: float = np.nan) -> dict:
    """ROIC, gross profitability, accruals, margins, cash conversion, leverage."""
    ta = _v(fin.total_assets())
    ebit, t = _v(fin.ebit()), fin.effective_tax_rate()
    invested = _v(fin.total_debt(), 0, 0.0) + _v(fin.equity()) - _v(fin.cash(), 0, 0.0)
    rev = _v(fin.revenue())
    ni, cfo = _v(fin.net_income()), _v(fin.cfo())
    out = {
        "ROIC": ebit * (1 - t) / invested if invested and invested > 0 else np.nan,
        "ROE": ni / _v(fin.equity()) if _v(fin.equity()) > 0 else np.nan,
        "Gross profitability (GP/TA)": _v(fin.gross_profit()) / ta if ta else np.nan,
        "Gross margin": _v(fin.gross_profit()) / rev if rev else np.nan,
        "Operating margin": ebit / rev if rev else np.nan,
        "FCF margin": _v(fin.fcf()) / rev if rev else np.nan,
        "Cash conversion (CFO/NI)": cfo / ni if ni and ni > 0 else np.nan,
        "Sloan accruals (NI-CFO)/TA": (ni - cfo) / ta if ta else np.nan,
        "Net debt / EBITDA": (_v(fin.total_debt(), 0, 0.0) - _v(fin.cash(), 0, 0.0)) / _v(fin.ebitda())
        if _v(fin.ebitda()) and _v(fin.ebitda()) > 0 else np.nan,
        "Interest coverage (EBIT/int)": ebit / _v(fin.interest_expense()) if _v(fin.interest_expense()) else np.nan,
        "SBC / revenue": _v(fin.sbc(), 0, np.nan) / rev if rev else np.nan,
        "Revenue CAGR (3y)": fin.revenue_cagr(3),
    }
    if np.isfinite(market_cap) and market_cap > 0:
        out["FCF yield"] = _v(fin.fcf()) / market_cap
        out["Earnings yield"] = ni / market_cap
    return {k: float(v) if v is not None and np.isfinite(v) else np.nan for k, v in out.items()}


def fair_value_summary(price: float, estimates: dict) -> dict:
    """Combine valuation estimates into a single blended fair value.

    ``estimates`` maps method name -> (value, weight). Non-finite values are
    ignored. Returns blended value, upside and a margin-of-safety label.
    """
    vals = [(v, w) for v, w in estimates.values() if v is not None and np.isfinite(v) and v > 0 and w > 0]
    if not vals:
        return {"fair_value": np.nan, "upside": np.nan, "label": "Insufficient data"}
    # Weighted geometric mean: robust to one method producing an outlier.
    lv = np.array([np.log(v) for v, _ in vals])
    w = np.array([w for _, w in vals], dtype=float)
    fv = float(np.exp((lv * w).sum() / w.sum()))
    up = fv / price - 1 if price else np.nan
    if up > 0.30:
        label = "Significantly undervalued"
    elif up > 0.10:
        label = "Undervalued"
    elif up > -0.10:
        label = "Fairly valued"
    elif up > -0.30:
        label = "Overvalued"
    else:
        label = "Significantly overvalued"
    return {"fair_value": fv, "upside": up, "label": label}

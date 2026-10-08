"""News: market headlines by topic with a tone read, and a per-stock catalyst desk."""

import numpy as np
import pandas as pd
import streamlit as st

from sharkfin import catalysts, data, sentiment, ui

ui.header("News", "Market headlines by topic, and the events that tend to move a single stock before they're priced in.")

mode = st.segmented_control("View", ["Headlines", "Stock catalysts"], default="Headlines", label_visibility="collapsed")

CATEGORIES = {
    "Markets": "stock market economy Fed rates inflation",
    "Tech & AI": "technology stocks AI semiconductors",
    "Healthcare": "healthcare pharma biotech stocks FDA",
    "Energy": "energy oil gas stocks OPEC",
    "Financials": "banks financial stocks earnings",
    "M&A": "merger acquisition deal takeover",
    "Consumer": "consumer retail food beverage stocks",
    "Crypto": "bitcoin crypto ETF",
}
FORM_NAMES = {"10-K": "Annual report", "10-Q": "Quarterly report", "8-K": "Event"}


def _tone_line(arts: list):
    agg = sentiment.aggregate_sentiment(arts[:40])
    if not agg["n"]:
        return
    st.markdown(f"<div class='sf-muted' style='margin:.2rem 0 .6rem'>Overall tone "
                f"{ui.pill(agg['label'], ui.tone(agg['score'], 0.1))} across {agg['n']} stories: "
                f"{agg['positive']} positive, {agg['negative']} negative.</div>", unsafe_allow_html=True)


def render(q: str):
    with st.spinner("Loading headlines…"):
        arts = sentiment.rank_articles(data.news(q), q)
    if not arts:
        st.info("No recent stories found for this topic.")
        return
    _tone_line(arts)
    for a in arts[:30]:
        ui.news_item(a)


def _filings(sym: str):
    st.subheader("SEC filings", help="10-K = annual report, 10-Q = quarterly report, 8-K = a material event "
                                      "(results, a deal, an executive change, a restructuring).")
    filings = data.sec_filings(sym)
    edgar = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={sym}&type=&dateb=&owner=include&count=40"
    if filings.empty:
        st.info(f"No filings came back for {sym}. Non-US companies file elsewhere; for US companies SEC EDGAR "
                f"is sometimes briefly unavailable. You can [search EDGAR directly]({edgar}).")
        return
    src = filings["source"].iloc[0] if "source" in filings else "SEC EDGAR"
    f = filings.copy()
    f["Type"] = f["form"].map(FORM_NAMES).fillna(f["form"])
    f["Details"] = [(w if isinstance(w, str) and w.strip() else FORM_NAMES.get(fm, fm)) for w, fm in zip(f["what"], f["form"])]
    st.dataframe(f[["filed", "form", "Type", "Details", "url"]], hide_index=True, width="stretch", height=320, column_config={
        "filed": st.column_config.DateColumn("Filed", format="MMM D, YYYY", width="small"),
        "form": st.column_config.TextColumn("Form", width="small"),
        "Type": st.column_config.TextColumn(width="small"),
        "Details": st.column_config.TextColumn(width="large"),
        "url": st.column_config.LinkColumn("Document", display_text="Open", width="small")})
    st.caption(f"Source: {src}" + ("" if src == "SEC EDGAR" else f" (SEC EDGAR didn't answer, so this is Yahoo's copy of the same "
                                                                  f"filings). [Open on EDGAR]({edgar})"))

    tenk = f[f["form"] == "10-K"].head(2)
    st.subheader("What changed in the annual report",
                 help="Compares the Risk Factors section of the last two 10-Ks. Companies whose annual-report wording "
                      "changes a lot have tended to underperform afterwards ('Lazy Prices', Cohen, Malloy & Nguyen 2020).")
    if len(tenk) < 2:
        st.caption("Needs two annual reports (10-K) in the list above.")
        return
    st.caption(f"Compares the {tenk['filed'].iloc[1]:%Y} and {tenk['filed'].iloc[0]:%Y} reports. Most companies keep over "
               "90% of the wording; a big rewrite, especially new risk language, is worth reading.")
    if st.button("Compare the last two annual reports"):
        with st.spinner("Downloading and comparing both reports…"):
            new_t, old_t = data.sec_document_text(tenk["url"].iloc[0]), data.sec_document_text(tenk["url"].iloc[1])
        if not new_t or not old_t:
            st.warning("Couldn't download the reports right now. Use the Open links above to read them.")
            return
        ch = catalysts.filing_change(old_t, new_t)
        ui.metrics([
            {"label": "Wording kept", "value": ui.fmt_pct(ch["similarity"], 1),
             "help": "100% = identical wording year over year."},
            {"label": "Verdict", "value": ch["label"]},
            {"label": "Length change", "value": ui.fmt_pct(ch["length_change"], 0, True), "delta": ch["section"],
             "delta_color": "off", "delta_arrow": "off"},
        ], key="tenk")
        if ch["new_sentences"]:
            st.markdown("**New language this year (sample)**")
            for sent in ch["new_sentences"]:
                st.markdown(f"> {ui.esc(sent)}")


def catalysts_view():
    sym = ui.symbol_picker("cat")
    if not sym:
        return
    inf = data.info(sym)
    hist = data.history(sym, "2y")
    ad = data.analyst_data(sym)
    fin = data.financials(sym)
    earn = catalysts.earnings_summary(ad.get("earnings_dates"))
    ins = catalysts.insider_summary(ad.get("insider_transactions"))
    rb = catalysts.revision_balance(ad.get("eps_revisions"))
    bb = catalysts.net_buyback_yield(fin, ui.num(inf.get("marketCap")))
    vr = catalysts.volume_read(hist) if not hist.empty else {"note": "", "rel_volume_20d": np.nan}
    mkt = data.market_history("2y")
    beat = catalysts.earnings_beat_flag(ad.get("earnings_dates"), hist["Close"] if not hist.empty else pd.Series(dtype=float),
                                        mkt["Close"] if not mkt.empty else None)

    if beat["active"]:
        st.markdown(f"<div class='sf-card buy'>{ui.pill('Big earnings beat', 'pos')}<span class='sf-note'>"
                    f"{ui.h(beat['note'])}</span></div>", unsafe_allow_html=True)
        if sym not in st.session_state.watchlist and st.button(f"Add {sym} to my watchlist", key="beat_watch"):
            st.session_state.watchlist.append(sym)
            ui.save_state()
            st.rerun()

    ui.metrics([
        {"label": "Next earnings", "value": f"{earn['next_date']:%b %d}" if earn.get("next_date") is not None else None,
         "help": "The biggest scheduled catalyst. Trades held through it carry gap risk."},
        {"label": "Last EPS surprise", "value": ui.fmt_pct(earn["last_surprise"], 0, True),
         "delta": f"{earn['days_since']} days ago" if earn.get("days_since") is not None else None,
         "delta_color": "off", "delta_arrow": "off",
         "help": "How far reported EPS beat (+) or missed (−) the estimate. Big beats tend to keep drifting up for ~60 trading days."},
        {"label": "Insider buyers (6m)", "value": str(ins["buyers"]),
         "delta": ui.fmt_money(ins["buy_value"], 1) if ins["buy_value"] else None, "delta_color": "off", "delta_arrow": "off",
         "help": "Distinct insiders who bought on the open market. Buying says more than selling."},
        {"label": "EPS revisions (30d)", "value": ui.fmt_pct(rb, 0, True) if np.isfinite(rb) else None,
         "help": "Net share of analyst EPS revisions that were upward over the last 30 days."},
        {"label": "Net buyback yield", "value": ui.fmt_pct(bb, 1),
         "help": "Last year's buybacks minus share issuance, as a % of market cap. Positive = shrinking share count."},
    ], key="cat")

    notes = [(t, n) for t, n in (("Earnings", earn.get("note")), ("Big-beat flag", None if beat["active"] else beat["note"]),
                                 ("Insiders", ins.get("note")), ("Volume", vr.get("note"))) if n]
    if notes:
        st.markdown("<div class='sf-card'>" + "".join(f"<div class='row'><b>{t}</b> · {ui.h(n)}</div>" for t, n in notes)
                    + "</div>", unsafe_allow_html=True)
    t = ins.get("table")
    if isinstance(t, pd.DataFrame) and not t.empty:
        with st.expander("Insider transactions (6 months)"):
            t = t.copy()
            if "Value" in t:
                t["Value"] = pd.to_numeric(t["Value"], errors="coerce").map(lambda v: ui.fmt_money(v, 1) if v else "—")
            if "Shares" in t:
                t["Shares"] = pd.to_numeric(t["Shares"], errors="coerce").map(lambda v: ui.fmt_big(v, 1))
            st.dataframe(t, hide_index=True, width="stretch", column_config={
                "Start Date": st.column_config.DateColumn("Date", format="MMM D, YYYY"), "Text": "What happened"})
    _filings(sym)


if mode == "Stock catalysts":
    catalysts_view()
else:
    query = st.text_input("Search news", placeholder="Search any topic, e.g. Nvidia earnings, tariffs, rate cut",
                          label_visibility="collapsed")
    if query:
        render(query)
    else:
        tabs = st.tabs(list(CATEGORIES))
        for tab, (name, q) in zip(tabs, CATEGORIES.items()):
            with tab:
                render(q)

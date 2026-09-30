"""News desk: categorised market news ranked by relevance and recency, with sentiment."""

import numpy as np
import pandas as pd
import streamlit as st

from sharkfin import catalysts, data, sentiment, ui

st.title("News Desk")
mode = st.segmented_control("View", ["Headlines", "Catalysts"], default="Headlines",
                            help="Headlines: market news by topic. Catalysts: for one stock, the events that tend to move "
                                 "prices before they're fully priced in (earnings surprises, insider buying, buybacks, "
                                 "estimate revisions, SEC filings).")

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
    mcap = ui.num(inf.get("marketCap"))
    bb = catalysts.net_buyback_yield(fin, mcap)
    vr = catalysts.volume_read(hist) if not hist.empty else {"note": "No price data.", "rel_volume_20d": np.nan}

    c = st.columns(5)
    c[0].metric("Next earnings", f"{earn['next_date']:%b %d}" if earn.get("next_date") is not None else "—",
                help="Earnings reports are the biggest scheduled catalyst. Swing trades held through them carry gap risk.")
    c[1].metric("Last surprise", ui.fmt_pct(earn["last_surprise"], 0, True),
                f"{earn['days_since']} days ago" if earn.get("days_since") is not None else None, delta_color="off",
                help="How far reported EPS beat (+) or missed (−) the analyst estimate. Big beats tend to drift up for ~60 trading days.")
    c[2].metric("Insider buyers (6m)", ins["buyers"], ui.fmt_money(ins["buy_value"], 1) if ins["buy_value"] else None,
                delta_color="off", help="Distinct insiders who bought shares on the open market. Buying says more than selling.")
    c[3].metric("Estimate revisions (30d)", ui.fmt_pct(rb, 0, True) if np.isfinite(rb) else "—",
                help="Net share of analyst EPS revisions that were upward over the last 30 days.")
    c[4].metric("Net buyback yield", ui.fmt_pct(bb, 1),
                help="Last fiscal year's share buybacks minus share issuance, as a % of market cap. Positive means the company is shrinking its share count.")

    for title, note in (("Earnings drift", earn["note"]), ("Insiders", ins["note"]), ("Volume", vr["note"])):
        st.markdown(f"**{title}:** {ui.esc(note)}")
    if isinstance(ins.get("table"), pd.DataFrame) and not ins["table"].empty:
        with st.expander("Insider transactions (6 months)"):
            st.dataframe(ins["table"], hide_index=True, width="stretch")

    st.subheader("SEC filings", help="10-K = annual report, 10-Q = quarterly report, 8-K = a material event "
                                      "(deal, executive change, results, restructuring). Straight from SEC EDGAR.")
    filings = data.sec_filings(sym)
    if filings.empty:
        st.info("Couldn't reach SEC EDGAR for this ticker right now (or it isn't a US filer).")
        return
    eightk = filings[filings["form"] == "8-K"].head(8)
    if not eightk.empty:
        st.markdown("**Recent 8-K events**")
        for _, r in eightk.iterrows():
            st.markdown(f"- {r['filed']:%b %d, %Y}: {ui.esc(r['what'] or 'Event filing')} ([filing]({r['url']}))")
    st.dataframe(filings, hide_index=True, width="stretch", column_config={
        "filed": st.column_config.DateColumn("Filed"), "form": "Form", "reportDate": "Period", "what": "8-K items",
        "url": st.column_config.LinkColumn("Link", display_text="open")})

    tenk = filings[filings["form"] == "10-K"].head(2)
    st.subheader("What changed in the annual report",
                 help="Compares the Risk Factors section of the last two 10-Ks. Companies whose annual report wording "
                      "changes a lot have tended to underperform afterwards ('Lazy Prices', Cohen, Malloy & Nguyen 2020); "
                      "new risk language is often the first place bad news shows up.")
    if len(tenk) < 2:
        st.info("Need two 10-K filings to compare.")
    elif st.button("Compare the last two 10-Ks", help="Downloads both filings from EDGAR, so it takes a few seconds."):
        with st.spinner("Downloading and comparing filings…"):
            new_t, old_t = data.sec_document_text(tenk["url"].iloc[0]), data.sec_document_text(tenk["url"].iloc[1])
        if not new_t or not old_t:
            st.warning("Couldn't download the filings.")
        else:
            ch = catalysts.filing_change(old_t, new_t)
            m = st.columns(3)
            m[0].metric("Wording similarity", ui.fmt_pct(ch["similarity"], 1),
                        help="1 = identical wording year over year. Most companies sit above 90%; big drops are a flag.")
            m[1].metric("Verdict", ch["label"])
            m[2].metric("Length change", ui.fmt_pct(ch["length_change"], 0, True), ch["section"], delta_color="off")
            if ch["new_sentences"]:
                st.markdown("**New language this year (sample)**")
                for sent in ch["new_sentences"]:
                    st.markdown(f"> {ui.esc(sent)}")


query = st.text_input("Search news", placeholder="e.g. Nvidia earnings, tariffs, rate cut") if mode != "Catalysts" else ""


def render(q: str):
    with st.spinner("Loading…"):
        arts = sentiment.rank_articles(data.news(q), q)
    agg = sentiment.aggregate_sentiment(arts[:40])
    st.markdown(ui.pill(f"Sentiment {agg['label']} ({agg['score']:+.2f})", ui.tone(agg["score"], 0.1)) +
                f"<span class='sf-muted'>{agg['n']} stories · {agg['positive']} positive · {agg['negative']} negative</span>",
                unsafe_allow_html=True)
    if not arts:
        st.info("No news found.")
    for a in arts[:30]:
        when = f"{a['published']:%b %d %H:%M}" if a.get("published") else ""
        summary = sentiment.clean_text(a.get("summary", ""))
        st.markdown(f"{ui.pill(a['sentiment_label'], ui.tone(a['sentiment'], 0.25))} **[{ui.esc(a['title'])}]({a.get('link') or '#'})**  \n"
                    f"<span class='sf-muted'>{a.get('publisher', '')} · {when}</span>", unsafe_allow_html=True)
        if summary and summary.lower() not in a["title"].lower():
            st.caption(ui.esc(summary[:260]) + ("…" if len(summary) > 260 else ""))


if mode == "Catalysts":
    catalysts_view()
elif query:
    render(query)
else:
    tabs = st.tabs(list(CATEGORIES))
    for tab, (name, q) in zip(tabs, CATEGORIES.items()):
        with tab:
            render(q)

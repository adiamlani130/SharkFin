"""News desk: categorised market news ranked by relevance and recency, with sentiment."""

import streamlit as st

from sharkfin import data, sentiment, ui

st.title("News Desk")

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

query = st.text_input("Search news", placeholder="e.g. Nvidia earnings, tariffs, rate cut")


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


if query:
    render(query)
else:
    tabs = st.tabs(list(CATEGORIES))
    for tab, (name, q) in zip(tabs, CATEGORIES.items()):
        with tab:
            render(q)

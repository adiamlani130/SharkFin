# 🦈 SharkFin - AI-Powered Financial Intelligence

**The future of financial forecasting and modeling**

Full-featured stock analysis platform with AI predictions, portfolio tracking, and market intelligence.

##  Features

- ** Portfolio Management** - Track positions with real-time P&L
- ** Research Center** - Deep stock analysis with charts & news
- ** AI Predictions** - 4 ML models (Time-Series, Technical, ML, Fundamental)
- ** Top Performers** - AI-powered buy/sell recommendations across 650+ stocks
- ** Financial News** - Curated market news with ML relevance scoring

##  File Structure

```
sharkfin/
├── streamlit_main.py              # Main app (run this)
├── streamlit_home_page.py         # Home page
├── streamlit_portfolio_page.py    # Portfolio tracker
├── streamlit_research_page.py     # Stock research & news
├── streamlit_prediction_page.py   # AI predictions
├── streamlit_top_performers_page.py  # Market scanner
├── streamlit_utils.py             # Helper functions
├── streamlit_requirements.txt     # Dependencies
├── sharkfin_logo.png             # Logo image
└── README.md                      # This file
```

##  Local Setup

```bash
# Install dependencies
pip install -r streamlit_requirements.txt

# Run app
streamlit run streamlit_main.py
```

##  Deploy to Streamlit Cloud (FREE)

1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click "New app"
4. Select your repo
5. Set main file to `streamlit_main.py`
6. Deploy!

##  Deploy to Vercel

Streamlit apps require a server runtime. Use Streamlit Cloud instead, or:

1. Set up Python serverless functions on Vercel
2. Use a different framework (Next.js + Python API)

**Recommended:** Use Streamlit Cloud for easiest deployment.

##  Tech Stack

- **Frontend:** Streamlit
- **Data:** Yahoo Finance API, Google News RSS
- **ML:** scikit-learn (Random Forest, Linear Regression)
- **Charts:** Plotly
- **Deployment:** Streamlit Cloud

##  Usage

### Home
View market status and portfolio stats

### Portfolio
- Add/remove positions
- Track real-time P&L
- See total portfolio value

### Research
- Search stocks with autocomplete
- View candlestick charts (5D to 5Y timeframes)
- See 18 financial metrics
- Browse 7 news categories
- Get stock-specific news

### Predictions
- **Time-Series:** Moving Average & Linear Trend forecasts
- **Technical:** 24 indicators (RSI, MACD, MAs, Bollinger Bands, etc.)
- **Machine Learning:** Random Forest 30-day forecast
- **Fundamental:** P/E, PEG, earnings analysis

### Top Performers
- Scan 650+ stocks (S&P 500 + NASDAQ-100)
- AI scoring based on technical + fundamental + ML signals
- Top 5 BUY and Top 5 SELL recommendations


##  Configuration



### Data Storage
- Portfolio and watchlist saved to `portfolio.json` and `watchlist.json`
- **Note:** On Streamlit Cloud, these files reset on app restart
- For persistent storage, consider using Streamlit's database integrations

##  Notes

- **Free APIs:** Uses free Yahoo Finance + Google News RSS (no API keys needed)
- **Rate Limits:** Yahoo Finance may throttle heavy usage
- **Performance:** Initial load may be slow due to data fetching
- **Top Performers:** Full scan takes 2-3 minutes for 650+ stocks

##  Disclaimer

This software is for educational purposes only. Not financial advice. Consult a qualified financial advisor before making investment decisions.


---

**Built by the SharkFin team**

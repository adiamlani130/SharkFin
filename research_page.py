"""
Research Page - FIXED: No buttons inside forms
"""

import streamlit as st
import yfinance as yf
from utils import (get_news_from_api, format_time_ago, create_candlestick_chart, 
                   search_stock_symbol, generate_article_summary)
from datetime import datetime

class ResearchPage:
    def __init__(self):
        """Initialize research page"""
        if 'research_symbol' not in st.session_state:
            st.session_state.research_symbol = None
        if 'research_submitted' not in st.session_state:
            st.session_state.research_submitted = False
    
    def create_content(self):
        """Create research page content"""
        st.title("🔍 Research Center")
        
        today = datetime.now().strftime("%A, %B %d, %Y")
        st.caption(f"📅 {today}")
        
        st.markdown("---")
        
        # TWO SEARCH BARS - SIMPLIFIED (no forms, just direct input)
        search_col1, search_col2 = st.columns(2)
        
        with search_col1:
            st.markdown("**🔍 Search Stocks**")
            stock_query = st.text_input("Type symbol and press Enter:", key="stock_input",
                                        placeholder="e.g., AAPL",
                                        label_visibility="collapsed")
            
            # Auto-search on input change
            if stock_query and len(stock_query) >= 1:
                matches = search_stock_symbol(stock_query.upper())
                if matches:
                    selected = st.selectbox("Select:", matches, key="stock_sel")
                    if st.button("🔍 Research", key="go_research"):
                        st.session_state.research_symbol = selected
                        st.session_state.research_submitted = True
                        st.rerun()
        
        with search_col2:
            st.markdown("**📰 Search News**")
            news_query = st.text_input("Type keywords and press Enter:", key="news_input",
                                      placeholder="e.g., earnings",
                                      label_visibility="collapsed")
            
            if st.button("📰 Search", key="news_search_btn"):
                if news_query:
                    self.display_news_search(news_query)
                    return
        
        st.markdown("---")
        
        # If stock was searched
        if st.session_state.research_submitted and st.session_state.research_symbol:
            self.display_stock_research(st.session_state.research_symbol)
            
            if st.button("⬅️ Back to News"):
                st.session_state.research_submitted = False
                st.session_state.research_symbol = None
                st.rerun()
            return
        
        # Default: News categories
        st.markdown("### 📰 Latest Financial News")
        
        tab_all, tab_tech, tab_health, tab_energy, tab_finance, tab_mergers, tab_food = st.tabs([
            "All", "Tech", "Healthcare", "Energy", "Finance", "Mergers", "Food"
        ])
        
        categories = {
            "All": "financial markets economy stocks",
            "Tech": "technology stocks",
            "Healthcare": "healthcare pharma stocks",
            "Energy": "energy oil gas stocks",
            "Finance": "banking finance stocks",
            "Mergers": "mergers acquisitions",
            "Food": "food beverage consumer stocks"
        }
        
        tabs_map = {
            "All": tab_all,
            "Tech": tab_tech,
            "Healthcare": tab_health,
            "Energy": tab_energy,
            "Finance": tab_finance,
            "Mergers": tab_mergers,
            "Food": tab_food
        }
        
        for category_name, tab in tabs_map.items():
            with tab:
                self.display_category_news(categories[category_name])
    
    def display_category_news(self, query):
        """Display news for category"""
        with st.spinner("📡 Loading..."):
            articles = get_news_from_api(query, 50, st.session_state.news_cache)
        
        if articles:
            for article in articles[:25]:
                st.markdown(f"**{article.get('title', 'No title')}**")
                summary = generate_article_summary(
                    article.get('title', ''),
                    article.get('description', '')
                )
                st.caption(summary)
                source = article.get('source', {}).get('name', 'Unknown')
                time_ago = format_time_ago(article.get('publishedAt', ''))
                st.caption(f"📡 {source} • {time_ago}")
                st.markdown("---")
        else:
            st.info("No news available")
    
    def display_news_search(self, query):
        """Display news search results"""
        st.markdown(f"### 📰 Results: '{query}'")
        
        with st.spinner("🔍 Searching..."):
            articles = get_news_from_api(query, 30, st.session_state.news_cache)
        
        if articles:
            for article in articles[:20]:
                st.markdown(f"**{article.get('title', 'No title')}**")
                summary = generate_article_summary(
                    article.get('title', ''),
                    article.get('description', '')
                )
                st.write(summary)
                source = article.get('source', {}).get('name', 'Unknown')
                time_ago = format_time_ago(article.get('publishedAt', ''))
                st.caption(f"📡 {source} • {time_ago}")
                st.markdown("---")
        else:
            st.warning(f"No news found")
        
        if st.button("⬅️ Back"):
            st.rerun()
    
    def display_stock_research(self, symbol):
        """Display stock research"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="1y")
            
            if hist.empty:
                st.error(f"No data for {symbol}")
                return
            
            col_h1, col_h2 = st.columns([3, 1])
            
            with col_h1:
                st.markdown(f"## {symbol} - {info.get('longName', symbol)}")
            
            with col_h2:
                if symbol in st.session_state.watchlist:
                    if st.button("⭐ Remove", key="watch_btn"):
                        st.session_state.watchlist.remove(symbol)
                        st.session_state.save_data()
                        st.rerun()
                else:
                    if st.button("☆ Add Watchlist", key="watch_btn", type="primary"):
                        st.session_state.watchlist.append(symbol)
                        st.session_state.save_data()
                        st.rerun()
            
            st.markdown("---")
            st.markdown("### 📈 Price Chart")
            
            timeframes = {"5D": "5d", "1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y", "5Y": "5y"}
            selected_tf = st.radio("", list(timeframes.keys()), index=2, horizontal=True)
            
            chart_hist = ticker.history(period=timeframes[selected_tf])
            if not chart_hist.empty:
                fig = create_candlestick_chart(symbol, chart_hist, timeframes[selected_tf])
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            st.markdown("### 📊 Statistics")
            
            price = info.get('currentPrice', info.get('regularMarketPrice', 'N/A'))
            mcap = info.get('marketCap', 0)
            mcap_str = f"${mcap/1e9:.2f}B" if mcap > 1e9 else 'N/A'
            pe_str = f"{info.get('trailingPE', 0):.2f}" if info.get('trailingPE') else 'N/A'
            
            col1, col2, col3 = st.columns(3)
            
            stats = [
                ("Price", f"${price}"),
                ("Market Cap", mcap_str),
                ("P/E Ratio", pe_str),
                ("52W High", f"${info.get('fiftyTwoWeekHigh', 'N/A')}"),
                ("52W Low", f"${info.get('fiftyTwoWeekLow', 'N/A')}"),
                ("Volume", f"{info.get('volume', 0):,}"),
                ("Sector", info.get('sector', 'N/A')),
                ("Industry", str(info.get('industry', 'N/A'))[:25]),
                ("Employees", f"{info.get('fullTimeEmployees', 0):,}" if info.get('fullTimeEmployees') else 'N/A'),
            ]
            
            for i, (label, value) in enumerate(stats):
                with [col1, col2, col3][i % 3]:
                    st.metric(label, value)
            
            st.markdown("---")
            st.markdown(f"### 📰 {symbol} News")
            
            with st.spinner("Loading news..."):
                stock_news = get_news_from_api(f"{symbol} stock", 10, st.session_state.news_cache)
            
            if stock_news:
                for article in stock_news[:8]:
                    st.markdown(f"**{article.get('title', 'No title')}**")
                    summary = generate_article_summary(
                        article.get('title', ''),
                        article.get('description', '')
                    )
                    st.caption(summary)
                    source = article.get('source', {}).get('name', 'Unknown')
                    time_ago = format_time_ago(article.get('publishedAt', ''))
                    st.caption(f"📅 {source} • {time_ago}")
                    st.markdown("---")
            else:
                st.info("No news")
        
        except Exception as e:
            st.error(f"Error: {str(e)}")

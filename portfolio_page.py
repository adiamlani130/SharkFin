"""
Portfolio Page - Complete Desktop Layout
Left panel: Quick view + Holdings + Watchlist
Right panel: Detailed stock analysis when clicked
"""

import streamlit as st
import yfinance as yf
from utils import search_stock_symbol, create_candlestick_chart
import pandas as pd

class PortfolioPage:
    def __init__(self):
        """Initialize portfolio page"""
        if 'selected_holding' not in st.session_state:
            st.session_state.selected_holding = None
    
    def create_content(self):
        """Create portfolio page with desktop layout"""
        st.title("💼 Portfolio Manager")
        
        # Top bar: Add position form
        with st.expander("➕ Add New Position", expanded=False):
            add_col1, add_col2, add_col3, add_col4 = st.columns([2, 1, 1, 1])
            
            with add_col1:
                # Stock search with dropdown
                search_query = st.text_input("Stock Symbol", key="add_stock_search", 
                                            placeholder="Type symbol or company name...")
                
                if search_query:
                    matches = search_stock_symbol(search_query.upper())
                    if matches:
                        selected_symbol = st.selectbox("Select stock", matches, key="symbol_dropdown")
                    else:
                        selected_symbol = search_query.upper()
                else:
                    selected_symbol = ""
            
            with add_col2:
                shares = st.number_input("Shares", min_value=0.001, value=1.0, step=0.1,
                                        key="add_shares", format="%.3f")
            
            with add_col3:
                # Auto-fetch current price
                if selected_symbol:
                    try:
                        ticker = yf.Ticker(selected_symbol)
                        info = ticker.info
                        current_price = info.get('currentPrice', info.get('regularMarketPrice', 100.0))
                        buy_price = st.number_input("Price per Share ($)", value=float(current_price),
                                                   step=0.01, format="%.2f", key="add_price")
                    except:
                        buy_price = st.number_input("Price per Share ($)", value=100.0,
                                                   step=0.01, format="%.2f", key="add_price")
                else:
                    buy_price = st.number_input("Price per Share ($)", value=100.0,
                                               step=0.01, format="%.2f", key="add_price")
            
            with add_col4:
                st.write("")
                st.write("")
                if st.button("➕ Add", use_container_width=True, type="primary"):
                    if selected_symbol:
                        st.session_state.portfolio.append({
                            'symbol': selected_symbol,
                            'shares': shares,
                            'buy_price': buy_price
                        })
                        st.session_state.save_data()
                        st.success(f"✅ Added {shares:.3f} shares of {selected_symbol}")
                        st.rerun()
        
        st.markdown("---")
        
        # DESKTOP LAYOUT: Left panel + Right panel
        left_col, right_col = st.columns([1, 2])
        
        # ===== LEFT PANEL =====
        with left_col:
            # Quick View Box
            st.markdown("### 📊 Quick View")
            
            if st.session_state.portfolio:
                # Calculate totals
                total_value = 0
                total_cost = 0
                
                with st.spinner("Updating prices..."):
                    for pos in st.session_state.portfolio:
                        try:
                            ticker = yf.Ticker(pos['symbol'])
                            info = ticker.info
                            current_price = info.get('currentPrice', info.get('regularMarketPrice', pos['buy_price']))
                            pos['current_price'] = current_price
                            pos['value'] = current_price * pos['shares']
                            pos['cost'] = pos['buy_price'] * pos['shares']
                            total_value += pos['value']
                            total_cost += pos['cost']
                        except:
                            pos['current_price'] = pos['buy_price']
                            pos['value'] = pos['buy_price'] * pos['shares']
                            pos['cost'] = pos['buy_price'] * pos['shares']
                
                total_gl = total_value - total_cost
                gl_pct = (total_gl / total_cost * 100) if total_cost > 0 else 0
                
                # Summary box
                summary_box = st.container()
                with summary_box:
                    st.metric("Total Value", f"${total_value:,.2f}")
                    st.metric("Total Cost", f"${total_cost:,.2f}")
                    
                    gl_color = "green" if total_gl >= 0 else "red"
                    st.markdown(f"""
                        <div style='background-color: #1a1a1a; padding: 15px; border-radius: 8px; 
                                    border: 2px solid {gl_color}; margin: 10px 0;'>
                            <div style='color: #888; font-size: 13px;'>Net Gain/Loss</div>
                            <div style='color: {gl_color}; font-size: 24px; font-weight: bold;'>
                                ${total_gl:,.2f}
                            </div>
                            <div style='color: {gl_color}; font-size: 16px;'>
                                {gl_pct:+.2f}%
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                
                # Filter
                filter_query = st.text_input("🔍 Filter holdings", key="filter_holdings",
                                            placeholder="Type to filter...")
            
            st.markdown("---")
            
            # Your Holdings Section
            st.markdown("### 📁 Your Holdings")
            
            if st.session_state.portfolio:
                # Filter if query exists
                filtered_portfolio = st.session_state.portfolio
                if 'filter_query' in locals() and filter_query:
                    filtered_portfolio = [p for p in st.session_state.portfolio 
                                        if filter_query.upper() in p['symbol'].upper()]
                
                # Display each holding as clickable button
                for idx, pos in enumerate(filtered_portfolio):
                    gl = pos.get('value', 0) - pos.get('cost', 0)
                    gl_pct = (gl / pos.get('cost', 1) * 100) if pos.get('cost', 0) > 0 else 0
                    gl_color = "#00ff88" if gl >= 0 else "#ff4444"
                    
                    # Clickable holding card
                    button_label = f"{pos['symbol']} • {pos['shares']:.2f} shares"
                    
                    if st.button(button_label, key=f"holding_{idx}", use_container_width=True):
                        st.session_state.selected_holding = pos['symbol']
                        st.rerun()
                    
                    # Show mini stats below button
                    st.caption(f"Value: ${pos.get('value', 0):,.2f} • "
                             f"P/L: {gl_pct:+.1f}%")
                    st.markdown("---")
            else:
                st.info("No holdings yet. Add your first position above!")
            
            st.markdown("---")
            
            # Watchlist Section
            st.markdown("### ⭐ Watchlist")
            
            if st.session_state.watchlist:
                for symbol in st.session_state.watchlist:
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        if st.button(symbol, key=f"watch_{symbol}", use_container_width=True):
                            st.session_state.selected_holding = symbol
                            st.rerun()
                    with col_b:
                        if st.button("🗑️", key=f"del_watch_{symbol}"):
                            st.session_state.watchlist.remove(symbol)
                            st.session_state.save_data()
                            st.rerun()
            else:
                st.info("Watchlist empty")
        
        # ===== RIGHT PANEL =====
        with right_col:
            if st.session_state.selected_holding:
                self.display_detailed_analysis(st.session_state.selected_holding)
            else:
                # Show welcome message
                st.markdown("""
                    <div style='text-align: center; padding: 100px 50px; color: #888;'>
                        <h2>📊 Select a holding to view details</h2>
                        <p>Click on any stock from your holdings or watchlist to see:</p>
                        <ul style='text-align: left; display: inline-block;'>
                            <li>Interactive price chart</li>
                            <li>Technical analysis & indicators</li>
                            <li>Key statistics & fundamentals</li>
                            <li>AI-powered insights</li>
                        </ul>
                    </div>
                """, unsafe_allow_html=True)
    
    def display_detailed_analysis(self, symbol):
        """Display detailed analysis in right panel"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="1y")
            
            if hist.empty:
                st.error(f"No data available for {symbol}")
                return
            
            # Header
            col_h1, col_h2 = st.columns([3, 1])
            with col_h1:
                st.markdown(f"## {symbol}")
                company_name = info.get('longName', symbol)
                st.caption(company_name)
            with col_h2:
                if st.button("❌ Close", key="close_analysis"):
                    st.session_state.selected_holding = None
                    st.rerun()
            
            st.markdown("---")
            
            # Price Chart
            st.markdown("### 📈 Price Chart")
            
            timeframe_opt = st.radio("Timeframe", ["1M", "3M", "6M", "1Y", "5Y"], 
                                    index=2, horizontal=True, key="chart_tf")
            
            tf_map = {"1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y", "5Y": "5y"}
            chart_hist = ticker.history(period=tf_map[timeframe_opt])
            
            if not chart_hist.empty:
                fig = create_candlestick_chart(symbol, chart_hist, tf_map[timeframe_opt])
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # Current Stats
            st.markdown("### 📊 Current Statistics")
            
            price = info.get('currentPrice', info.get('regularMarketPrice', 'N/A'))
            
            stat_col1, stat_col2, stat_col3 = st.columns(3)
            with stat_col1:
                st.metric("Current Price", f"${price}" if isinstance(price, (int, float)) else price)
            with stat_col2:
                day_change = info.get('regularMarketChangePercent', 0)
                st.metric("Day Change", f"{day_change:.2f}%", delta=f"{day_change:+.2f}%")
            with stat_col3:
                volume = info.get('volume', 0)
                st.metric("Volume", f"{volume:,}")
            
            st.markdown("---")
            
            # Technical Analysis
            st.markdown("### 🔧 Technical Indicators")
            
            from utils import calculate_rsi
            
            prices = hist['Close'].tolist()
            rsi = calculate_rsi(prices)
            ma_20 = sum(prices[-20:]) / 20 if len(prices) >= 20 else price
            ma_50 = sum(prices[-50:]) / 50 if len(prices) >= 50 else price
            
            tech_col1, tech_col2, tech_col3 = st.columns(3)
            with tech_col1:
                st.metric("RSI (14)", f"{rsi:.1f}")
            with tech_col2:
                st.metric("MA (20)", f"${ma_20:.2f}")
            with tech_col3:
                st.metric("MA (50)", f"${ma_50:.2f}")
            
            # Trading signal
            score = 0
            if rsi < 40:
                score += 2
            elif rsi > 60:
                score -= 2
            if price > ma_20:
                score += 1
            if price > ma_50:
                score += 1
            
            if score >= 3:
                st.success("🚀 **Technical Signal: STRONG BUY**")
            elif score >= 1:
                st.success("📈 **Technical Signal: BUY**")
            elif score <= -3:
                st.error("🚨 **Technical Signal: STRONG SELL**")
            elif score <= -1:
                st.warning("📉 **Technical Signal: SELL**")
            else:
                st.info("⏸️ **Technical Signal: NEUTRAL**")
            
            st.markdown("---")
            
            # Fundamentals
            st.markdown("### 💰 Key Fundamentals")
            
            fund_col1, fund_col2, fund_col3 = st.columns(3)
            
            with fund_col1:
                pe = info.get('trailingPE', None)
                st.metric("P/E Ratio", f"{pe:.2f}" if pe else "N/A")
                
                eps = info.get('trailingEps', None)
                st.metric("EPS", f"${eps:.2f}" if eps else "N/A")
            
            with fund_col2:
                mcap = info.get('marketCap', 0)
                mcap_str = f"${mcap/1e9:.2f}B" if mcap > 1e9 else "N/A"
                st.metric("Market Cap", mcap_str)
                
                div_yield = info.get('dividendYield', 0)
                div_str = f"{div_yield*100:.2f}%" if div_yield else "N/A"
                st.metric("Dividend Yield", div_str)
            
            with fund_col3:
                high_52w = info.get('fiftyTwoWeekHigh', None)
                st.metric("52W High", f"${high_52w:.2f}" if high_52w else "N/A")
                
                low_52w = info.get('fiftyTwoWeekLow', None)
                st.metric("52W Low", f"${low_52w:.2f}" if low_52w else "N/A")
            
            st.markdown("---")
            
            # AI Tips & Advice
            st.markdown("### 🤖 AI Insights")
            
            # Generate insights based on data
            insights = []
            
            if rsi < 30:
                insights.append("⚠️ **Oversold Territory**: RSI suggests stock may be undervalued")
            elif rsi > 70:
                insights.append("⚠️ **Overbought Territory**: RSI suggests stock may be overvalued")
            
            if pe and 0 < pe < 15:
                insights.append("✅ **Attractive Valuation**: P/E ratio below market average")
            elif pe and pe > 30:
                insights.append("⚠️ **High Valuation**: P/E ratio above market average")
            
            if price > ma_20 > ma_50:
                insights.append("📈 **Bullish Trend**: Price trading above moving averages")
            elif price < ma_20 < ma_50:
                insights.append("📉 **Bearish Trend**: Price trading below moving averages")
            
            if insights:
                for insight in insights:
                    st.markdown(f"- {insight}")
            else:
                st.info("No significant insights at this time")
            
        except Exception as e:
            st.error(f"Error loading data for {symbol}: {str(e)}")

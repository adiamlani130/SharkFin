"""
Home Page - Perfect Version
Ticker strip with colors, centered logo, compact layout
"""

import streamlit as st
from datetime import datetime
import pytz
import yfinance as yf

class HomePage:
    def __init__(self):
        """Initialize home page"""
        pass
    
    def get_ticker_data(self):
        """Get real-time ticker data for major stocks"""
        symbols = ["SPY", "QQQ", "DIA", "AAPL", "MSFT", "NVDA", "TSLA", 
           "GOOGL", "AMZN", "JPM", "XOM", "BTC-USD"]
        data = []
        
        for sym in symbols:
            try:
                ticker = yf.Ticker(sym)
                info = ticker.info
                price = info.get('currentPrice', info.get('regularMarketPrice', 0))
                change = info.get('regularMarketChangePercent', 0)
                data.append((sym, price, change))
            except Exception as e:
                # Fallback if API fails
                pass
        
        return data
    
    def create_content(self):
        """Display home page with ticker strip and quick access"""
        
        # ===== TICKER STRIP AT TOP =====
        ticker_data = self.get_ticker_data()
        
        # Build ticker HTML with proper colors
        ticker_items = []
        for sym, price, change in ticker_data:
            arrow = "▲" if change >= 0 else "▼"
            color = "#00ff88" if change >= 0 else "#ff4444"
            
            ticker_items.append(
                f'<span style="color:{color};font-weight:bold;">{sym} ${price:.2f} {arrow} {abs(change):.2f}%</span>'
            )

        # Join with separators
        ticker_html = ' &nbsp;|&nbsp; '.join(ticker_items * 4)
        
        # Display ticker strip
        st.markdown(f"""
        <style>
        .ticker-container {{
            background: linear-gradient(90deg, #1a1a1a 0%, #2a2a2a 50%, #1a1a1a 100%);
            padding: 12px 0;
            overflow: hidden;
            border-bottom: 2px solid #00aa55;
            margin-bottom: 30px;
        }}
        </style>
        <div class="ticker-container">
            <marquee behavior="scroll" direction="left" scrollamount="4">
                {ticker_html}
            </marquee>
        </div>
        """, unsafe_allow_html=True)


        
        # ===== CENTERED LOGO SECTION =====
        col_left, col_center, col_right = st.columns([1.5, 1, 1.5])
        
        with col_center:
            # SharkFin Logo - centered
            try:
                st.image("sharkfin_logo.png", width=280)
            except:
                st.markdown(
                    "<h1 style='text-align: center; font-size: 48px; margin: 0;'>🦈 SharkFin</h1>",
                    unsafe_allow_html=True
                )
            
            # Tagline
            st.markdown(
                "<h4 style='text-align: center; color: #00d4ff; margin: 15px auto; font-weight: normal; max-width: 500px;'>"
                "The Future of Financial \nForecasting and Modeling"
                "</h4>",
                unsafe_allow_html=True
            )
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # ===== MARKET STATUS =====
            ny_tz = pytz.timezone('America/New_York')
            now = datetime.now(ny_tz)
            is_weekend = now.weekday() >= 5  # Saturday=5, Sunday=6
            
            # Market open: 9:30 AM - 4:00 PM ET, weekdays only
            market_open = False
            if not is_weekend:
                if now.hour > 9 or (now.hour == 9 and now.minute >= 30):
                    if now.hour < 16:
                        market_open = True
            
            status_text = "🟢 Market Open" if market_open else "🔴 Market Closed"
            status_color = "#00ff88" if market_open else "#ff4444"
            
            st.markdown(f"""
                <div style='
                    background-color: #1a1a1a;
                    padding: 15px;
                    border-radius: 10px;
                    text-align: center;
                    border: 2px solid {status_color};
                    margin: 15px 0;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                '>
                    <h3 style='color: {status_color}; margin: 0; font-size: 22px;'>
                        {status_text}
                    </h3>
                    <p style='color: #888888; font-size: 12px; margin: 5px 0 0 0;'>
                        NYSE: 9:30 AM - 4:00 PM ET
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # ===== QUICK STATS - 3 BOXES =====
            stat_col1, stat_col2, stat_col3 = st.columns(3)
            
            with stat_col1:
                st.markdown(f"""
                    <div style='
                        background-color: #1a1a1a;
                        padding: 18px 12px;
                        border-radius: 10px;
                        text-align: center;
                        border: 2px solid #2a2a2a;
                        transition: all 0.3s;
                    '>
                        <div style='font-size: 36px; margin-bottom: 10px;'>📊</div>
                        <div style='font-size: 24px; font-weight: bold; color: #00ff88; margin-bottom: 5px;'>
                            {len(st.session_state.portfolio)}
                        </div>
                        <div style='font-size: 11px; color: #888888; letter-spacing: 1px;'>
                            POSITIONS
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            with stat_col2:
                st.markdown(f"""
                    <div style='
                        background-color: #1a1a1a;
                        padding: 18px 12px;
                        border-radius: 10px;
                        text-align: center;
                        border: 2px solid #2a2a2a;
                        transition: all 0.3s;
                    '>
                        <div style='font-size: 36px; margin-bottom: 10px;'>⭐</div>
                        <div style='font-size: 24px; font-weight: bold; color: #00ff88; margin-bottom: 5px;'>
                            {len(st.session_state.watchlist)}
                        </div>
                        <div style='font-size: 11px; color: #888888; letter-spacing: 1px;'>
                            WATCHLIST
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            with stat_col3:
                st.markdown("""
                    <div style='
                        background-color: #1a1a1a;
                        padding: 18px 12px;
                        border-radius: 10px;
                        text-align: center;
                        border: 2px solid #2a2a2a;
                        transition: all 0.3s;
                    '>
                        <div style='font-size: 36px; margin-bottom: 10px;'>🤖</div>
                        <div style='font-size: 15px; font-weight: bold; color: #00ff88; margin-bottom: 5px;'>
                            ML-POWERED
                        </div>
                        <div style='font-size: 11px; color: #888888; letter-spacing: 1px;'>
                            MARKET ANALYSIS
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br><br>", unsafe_allow_html=True)
            
            # ===== QUICK NAVIGATION BUTTONS =====
            st.markdown("### 🚀 Quick Access")
            
            nav_col1, nav_col2 = st.columns(2)
            
            with nav_col1:
                if st.button("💼 View Portfolio", width="stretch", type="primary", key="nav_portfolio"):
                    st.session_state.current_page = "Portfolio"
                    st.rerun()
                
                if st.button("🔮 Comprehensive Predictions", width="stretch", key="nav_predictions"):
                    st.session_state.current_page = "Predictions"
                    st.rerun()
            
            with nav_col2:
                if st.button("🔍 Research Stocks", width="stretch", type="primary", key="nav_research"):
                    st.session_state.current_page = "Research"
                    st.rerun()
                
                if st.button("🏆 Top Performers", width="stretch", key="nav_top"):
                    st.session_state.current_page = "Top Performers"
                    st.rerun()
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # ===== FEATURE HIGHLIGHTS =====
            st.markdown("""
                <div style='text-align: center; color: #888888; font-size: 13px; line-height: 2;'>
                    <p style='margin: 5px 0;'>📈 Real-time Portfolio Tracking • 🔍 Deep Stock Research</p>
                    <p style='margin: 5px 0;'>🤖 4 Advanced Prediction Models • 📰 Curated News</p>
                    <p style='margin: 5px 0;'>🏆 Market-Wide Analysis • 💰 Fundamental Insights</p>
                </div>
            """, unsafe_allow_html=True)

"""
Top Performers Page - Market-wide AI analysis
Features: Green/red borders, 1-column layout, detailed reasoning
"""

import streamlit as st
import yfinance as yf
import numpy as np
from utils import get_all_symbols, calculate_rsi
from datetime import datetime
import concurrent.futures
def create_content(self):
    # Force sidebar visible on non-home pages
    st.sidebar.markdown("")  # This forces sidebar to stay open
    
    st.title("💼 Portfolio Manager")  # existing code continues...
class TopPerformersPage:
    def __init__(self):
        """Initialize top performers page"""
        pass
    
    def create_content(self):
        """Create top performers page"""
        st.title("🏆 Top Performers")
        st.markdown("### 🤖 AI-Powered Market Analysis")
        st.caption("Comprehensive analysis across S&P 500 + NASDAQ-100 using ML, technicals, and fundamentals")
        
        st.markdown("---")
        
        # Info box
        st.info("⚠️ **Full market scan** analyzes 650+ stocks using 3 scoring models. Takes ~2-3 minutes.")
        
        st.markdown("---")
        
        # Run analysis button
        if st.button("🔄 Run Full Market Analysis", use_container_width=True, type="primary"):
            self.run_analysis()
        else:
            # Welcome screen
            st.markdown("""
                <div style='text-align: center; padding: 50px; color: #888;'>
                    <h3>Ready to analyze the entire market</h3>
                    <p>Our AI will scan 650+ stocks and identify:</p>
                    <ul style='text-align: left; display: inline-block;'>
                        <li><strong>Top 5 BUY recommendations</strong> - Best opportunities</li>
                        <li><strong>Top 5 SELL warnings</strong> - Stocks to avoid</li>
                    </ul>
                    <br><br>
                    <p><strong>Analysis includes:</strong></p>
                    <ul style='text-align: left; display: inline-block;'>
                        <li>Technical indicators (RSI, MAs, momentum)</li>
                        <li>Fundamental metrics (P/E, earnings growth)</li>
                        <li>ML momentum signals (price trends)</li>
                    </ul>
                </div>
            """, unsafe_allow_html=True)
    
    def analyze_stock_fast(self, symbol):
        """Fast analysis for single stock - optimized"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get only what we need - faster
            hist = ticker.history(period="3mo")
            if hist.empty or len(hist) < 20:
                return None
            
            info = ticker.info
            prices = hist['Close'].tolist()
            volumes = hist['Volume'].tolist()
            current_price = prices[-1]
            
            # TECHNICAL SCORE
            rsi = calculate_rsi(prices)
            ma_20 = sum(prices[-20:]) / 20
            ma_50 = sum(prices[-50:]) / 50 if len(prices) >= 50 else ma_20
            
            tech_score = 0
            tech_reasons = []
            
            if rsi < 30:
                tech_score += 3
                tech_reasons.append("RSI oversold (<30)")
            elif rsi < 40:
                tech_score += 2
                tech_reasons.append("RSI below 40")
            elif rsi > 70:
                tech_score -= 3
                tech_reasons.append("RSI overbought (>70)")
            elif rsi > 60:
                tech_score -= 2
                tech_reasons.append("RSI above 60")
            
            if current_price > ma_20 > ma_50:
                tech_score += 2
                tech_reasons.append("Bullish MA trend")
            elif current_price > ma_20:
                tech_score += 1
                tech_reasons.append("Above MA(20)")
            elif current_price < ma_20:
                tech_score -= 1
                tech_reasons.append("Below MA(20)")
            
            # Volume check
            avg_vol = sum(volumes[-10:]) / 10 if len(volumes) >= 10 else volumes[-1]
            if volumes[-1] > avg_vol * 1.5:
                tech_score += 1
                tech_reasons.append("High volume")
            
            # FUNDAMENTAL SCORE
            pe = info.get('trailingPE', 0)
            eps_growth = info.get('earningsGrowth', 0)
            profit_margin = info.get('profitMargins', 0)
            
            fund_score = 0
            fund_reasons = []
            
            if pe and 0 < pe < 15:
                fund_score += 2
                fund_reasons.append(f"Low P/E ({pe:.1f})")
            elif pe and 15 <= pe < 25:
                fund_score += 1
                fund_reasons.append(f"Fair P/E ({pe:.1f})")
            elif pe and pe > 35:
                fund_score -= 2
                fund_reasons.append(f"High P/E ({pe:.1f})")
            
            if eps_growth and eps_growth > 0.15:
                fund_score += 2
                fund_reasons.append(f"Strong growth ({eps_growth*100:.0f}%)")
            elif eps_growth and eps_growth > 0.05:
                fund_score += 1
                fund_reasons.append(f"Positive growth ({eps_growth*100:.0f}%)")
            elif eps_growth and eps_growth < -0.1:
                fund_score -= 2
                fund_reasons.append(f"Declining earnings ({eps_growth*100:.0f}%)")
            
            if profit_margin and profit_margin > 0.15:
                fund_score += 1
                fund_reasons.append(f"High margins ({profit_margin*100:.0f}%)")
            
            # ML MOMENTUM SCORE
            week_change = ((prices[-1] - prices[-5]) / prices[-5]) if len(prices) >= 5 else 0
            month_change = ((prices[-1] - prices[-20]) / prices[-20]) if len(prices) >= 20 else 0
            
            ml_score = 0
            ml_reasons = []
            
            if month_change > 0.15:
                ml_score += 3
                ml_reasons.append(f"Strong 1M momentum (+{month_change*100:.0f}%)")
            elif month_change > 0.05:
                ml_score += 1
                ml_reasons.append(f"Positive 1M trend (+{month_change*100:.0f}%)")
            elif month_change < -0.15:
                ml_score -= 3
                ml_reasons.append(f"Weak 1M momentum ({month_change*100:.0f}%)")
            elif month_change < -0.05:
                ml_score -= 1
                ml_reasons.append(f"Negative 1M trend ({month_change*100:.0f}%)")
            
            if week_change > 0.05:
                ml_score += 1
                ml_reasons.append(f"Weekly momentum (+{week_change*100:.0f}%)")
            elif week_change < -0.05:
                ml_score -= 1
                ml_reasons.append(f"Weekly decline ({week_change*100:.0f}%)")
            
            # TOTAL SCORE
            total_score = tech_score + fund_score + ml_score
            
            return {
                'symbol': symbol,
                'name': info.get('longName', symbol)[:35],
                'price': current_price,
                'tech_score': tech_score,
                'fund_score': fund_score,
                'ml_score': ml_score,
                'total_score': total_score,
                'rsi': rsi,
                'pe': pe if pe else 0,
                'change_1w': week_change * 100,
                'change_1m': month_change * 100,
                'tech_reasons': tech_reasons[:3],
                'fund_reasons': fund_reasons[:2],
                'ml_reasons': ml_reasons[:2]
            }
        
        except:
            return None
    
    def run_analysis(self):
        """Run full market analysis with parallel processing"""
        all_symbols = get_all_symbols()
        
        st.markdown("### 🔄 Analysis in Progress")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        total = len(all_symbols)
        
        # PARALLEL PROCESSING for speed
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_symbol = {executor.submit(self.analyze_stock_fast, symbol): symbol 
                               for symbol in all_symbols}
            
            completed = 0
            for future in concurrent.futures.as_completed(future_to_symbol):
                result = future.result()
                if result:
                    results.append(result)
                
                completed += 1
                progress = completed / total
                progress_bar.progress(progress)
                status_text.text(f"Analyzed {completed}/{total} stocks ({progress*100:.0f}%)")
        
        progress_bar.empty()
        status_text.empty()
        
        if not results:
            st.error("❌ No stocks could be analyzed")
            return
        
        # Sort by score
        results_sorted = sorted(results, key=lambda x: x['total_score'], reverse=True)
        
        # Get top buys and sells
        top_buys = [r for r in results_sorted if r['total_score'] > 0][:5]
        top_sells = [r for r in results_sorted if r['total_score'] < 0][-5:]
        top_sells.reverse()
        
        st.success(f"✅ **Analysis Complete!** Analyzed {len(results)} stocks")
        
        st.markdown("---")
        
        # DISPLAY RESULTS - 1 COLUMN LAYOUT
        
        # TOP 5 BUYS
        st.markdown("### 🚀 Top 5 Stocks to BUY")
        st.caption("Highest-rated opportunities based on combined AI scoring")
        
        if top_buys:
            for i, stock in enumerate(top_buys, 1):
                # Green border box
                st.markdown(f"""
                    <div style='
                        background-color: #1a1a1a;
                        padding: 20px;
                        border-radius: 10px;
                        border: 3px solid #00ff88;
                        margin: 15px 0;
                        box-shadow: 0 4px 12px rgba(0, 255, 136, 0.2);
                    '>
                        <h3 style='color: #00ff88; margin: 0;'>#{i} {stock['symbol']}</h3>
                        <p style='color: #888; margin: 5px 0 15px 0;'>{stock['name']}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                # Stats in columns
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Price", f"${stock['price']:.2f}")
                with col2:
                    st.metric("1W Change", f"{stock['change_1w']:+.1f}%")
                with col3:
                    st.metric("1M Change", f"{stock['change_1m']:+.1f}%")
                with col4:
                    st.metric("Total Score", f"{stock['total_score']:+d}", 
                             delta="BUY" if stock['total_score'] >= 5 else "")
                
                # Detailed breakdown
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    st.markdown(f"**📈 Technical: {stock['tech_score']:+d}**")
                    for reason in stock['tech_reasons']:
                        st.caption(f"• {reason}")
                    st.caption(f"RSI: {stock['rsi']:.1f}")
                
                with col_b:
                    st.markdown(f"**💰 Fundamental: {stock['fund_score']:+d}**")
                    for reason in stock['fund_reasons']:
                        st.caption(f"• {reason}")
                    if stock['pe'] > 0:
                        st.caption(f"P/E: {stock['pe']:.1f}")
                
                with col_c:
                    st.markdown(f"**🤖 ML Momentum: {stock['ml_score']:+d}**")
                    for reason in stock['ml_reasons']:
                        st.caption(f"• {reason}")
                
                st.markdown("---")
        else:
            st.info("No strong buy signals detected")
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # TOP 5 SELLS
        st.markdown("### 🚨 Top 5 Stocks to SELL/AVOID")
        st.caption("Lowest-rated stocks with bearish signals")
        
        if top_sells:
            for i, stock in enumerate(top_sells, 1):
                # Red border box
                st.markdown(f"""
                    <div style='
                        background-color: #1a1a1a;
                        padding: 20px;
                        border-radius: 10px;
                        border: 3px solid #ff4444;
                        margin: 15px 0;
                        box-shadow: 0 4px 12px rgba(255, 68, 68, 0.2);
                    '>
                        <h3 style='color: #ff4444; margin: 0;'>#{i} {stock['symbol']}</h3>
                        <p style='color: #888; margin: 5px 0 15px 0;'>{stock['name']}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                # Stats
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Price", f"${stock['price']:.2f}")
                with col2:
                    st.metric("1W Change", f"{stock['change_1w']:+.1f}%")
                with col3:
                    st.metric("1M Change", f"{stock['change_1m']:+.1f}%")
                with col4:
                    st.metric("Total Score", f"{stock['total_score']:+d}",
                             delta="SELL" if stock['total_score'] <= -5 else "")
                
                # Detailed breakdown
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    st.markdown(f"**📉 Technical: {stock['tech_score']:+d}**")
                    for reason in stock['tech_reasons']:
                        st.caption(f"• {reason}")
                    st.caption(f"RSI: {stock['rsi']:.1f}")
                
                with col_b:
                    st.markdown(f"**💸 Fundamental: {stock['fund_score']:+d}**")
                    for reason in stock['fund_reasons']:
                        st.caption(f"• {reason}")
                    if stock['pe'] > 0:
                        st.caption(f"P/E: {stock['pe']:.1f}")
                
                with col_c:
                    st.markdown(f"**🤖 ML Momentum: {stock['ml_score']:+d}**")
                    for reason in stock['ml_reasons']:
                        st.caption(f"• {reason}")
                
                st.markdown("---")
        else:
            st.info("No strong sell signals detected")
        
        # Disclaimer
        st.markdown("---")
        st.warning("""
            ⚠️ **DISCLAIMER**: These recommendations are generated by AI for educational purposes only. 
            This is NOT financial advice. Always conduct your own research and consult with a qualified 
            financial advisor before making investment decisions. Past performance does not guarantee future results.
        """)

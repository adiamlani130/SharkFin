"""
Prediction Page - FIXED: No form errors
"""

import streamlit as st
import yfinance as yf
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from utils import calculate_rsi, search_stock_symbol, create_forecast_chart

class PredictionPage:
    def __init__(self):
        if 'predict_symbol' not in st.session_state:
            st.session_state.predict_symbol = None
        if 'predict_submitted' not in st.session_state:
            st.session_state.predict_submitted = False
    
    def create_content(self):
        st.title("🔮 Stock Predictions")
        st.caption("AI forecasting with 4 models")
        st.markdown("---")
        
        # Simple search - NO FORMS
        col1, col2 = st.columns([3, 1])
        
        with col1:
            symbol_query = st.text_input("Enter stock symbol:", key="pred_input",
                                         placeholder="e.g., AAPL")
            
            if symbol_query and len(symbol_query) >= 1:
                matches = search_stock_symbol(symbol_query.upper())
                if matches:
                    selected = st.selectbox("Select:", matches, key="pred_sel")
                    if st.button("🔮 Predict", key="pred_btn", type="primary"):
                        st.session_state.predict_symbol = selected
                        st.session_state.predict_submitted = True
                        st.rerun()
        
        st.markdown("---")
        
        if st.session_state.predict_submitted and st.session_state.predict_symbol:
            self.display_predictions(st.session_state.predict_symbol)
            
            if st.button("⬅️ New Prediction"):
                st.session_state.predict_submitted = False
                st.session_state.predict_symbol = None
                st.rerun()
        else:
            st.info("Enter a symbol to see AI forecasts")
    
    def display_predictions(self, symbol):
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="1y")
            
            if hist.empty:
                st.error(f"No data for {symbol}")
                return
            
            current_price = hist['Close'].iloc[-1]
            
            st.markdown(f"## 🔮 {symbol} - {info.get('longName', symbol)}")
            st.metric("Current Price", f"${current_price:.2f}")
            st.markdown("---")
            
            tab1, tab2, tab3, tab4 = st.tabs([
                "📊 Time-Series", "📈 Technical", "🤖 ML", "💰 Fundamental"
            ])
            
            prices = hist['Close'].tolist()
            volumes = hist['Volume'].tolist()
            
            # TAB 1: Time-Series with charts
            with tab1:
                st.subheader("📊 Time-Series Forecasting")
                
                ma_20 = sum(prices[-20:]) / 20 if len(prices) >= 20 else current_price
                ma_forecast = [ma_20 + np.random.normal(0, current_price * 0.01) for _ in range(30)]
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("1 Week", f"${ma_forecast[6]:.2f}", 
                             f"{((ma_forecast[6] - current_price) / current_price * 100):+.1f}%")
                with col2:
                    st.metric("2 Weeks", f"${ma_forecast[13]:.2f}",
                             f"{((ma_forecast[13] - current_price) / current_price * 100):+.1f}%")
                with col3:
                    st.metric("1 Month", f"${ma_forecast[29]:.2f}",
                             f"{((ma_forecast[29] - current_price) / current_price * 100):+.1f}%")
                
                fig_ma = create_forecast_chart(symbol, prices, ma_forecast, "MA Forecast")
                if fig_ma:
                    st.plotly_chart(fig_ma, use_container_width=True)
                
                st.markdown("#### Linear Trend")
                x = np.arange(len(prices)).reshape(-1, 1)
                y = np.array(prices)
                model = LinearRegression()
                model.fit(x, y)
                future_x = np.arange(len(prices), len(prices) + 30).reshape(-1, 1)
                linear_forecast = model.predict(future_x).tolist()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("1 Week", f"${linear_forecast[6]:.2f}",
                             f"{((linear_forecast[6] - current_price) / current_price * 100):+.1f}%")
                with col2:
                    st.metric("2 Weeks", f"${linear_forecast[13]:.2f}",
                             f"{((linear_forecast[13] - current_price) / current_price * 100):+.1f}%")
                with col3:
                    st.metric("1 Month", f"${linear_forecast[29]:.2f}",
                             f"{((linear_forecast[29] - current_price) / current_price * 100):+.1f}%")
                
                fig_lin = create_forecast_chart(symbol, prices, linear_forecast, "Linear Forecast")
                if fig_lin:
                    st.plotly_chart(fig_lin, use_container_width=True)
            
            # TAB 2: Technical
            with tab2:
                st.subheader("📈 Technical Analysis")
                
                rsi = calculate_rsi(prices)
                ma_10 = sum(prices[-10:]) / 10 if len(prices) >= 10 else current_price
                ma_20 = sum(prices[-20:]) / 20 if len(prices) >= 20 else current_price
                ma_50 = sum(prices[-50:]) / 50 if len(prices) >= 50 else current_price
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("RSI (14)", f"{rsi:.1f}")
                with col2:
                    st.metric("MA (20)", f"${ma_20:.2f}")
                with col3:
                    st.metric("MA (50)", f"${ma_50:.2f}")
                
                score = 0
                if rsi < 40:
                    score += 2
                elif rsi > 60:
                    score -= 2
                if current_price > ma_20:
                    score += 1
                if current_price > ma_50:
                    score += 1
                
                st.markdown("---")
                if score >= 3:
                    st.success("🚀 STRONG BUY")
                elif score >= 1:
                    st.success("📈 BUY")
                elif score <= -3:
                    st.error("🚨 STRONG SELL")
                elif score <= -1:
                    st.warning("📉 SELL")
                else:
                    st.info("⏸️ NEUTRAL")
            
            # TAB 3: ML with chart
            with tab3:
                st.subheader("🤖 ML Forecast")
                
                with st.spinner("Training..."):
                    X = []
                    y = []
                    
                    for i in range(20, len(prices)):
                        features = [
                            prices[i-1],
                            sum(prices[i-5:i])/5,
                            sum(prices[i-10:i])/10,
                            sum(prices[i-20:i])/20,
                            calculate_rsi(prices[:i]),
                            volumes[i-1] / (sum(volumes[i-10:i])/10) if sum(volumes[i-10:i]) > 0 else 1,
                            (prices[i-1] - prices[i-5]) / prices[i-5] if prices[i-5] != 0 else 0,
                        ]
                        X.append(features)
                        y.append(prices[i])
                    
                    model = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42)
                    model.fit(X, y)
                    
                    ml_forecast = []
                    last_features = X[-1].copy()
                    
                    for day in range(30):
                        pred = model.predict([last_features])[0]
                        pred += np.random.normal(0, current_price * 0.015)
                        ml_forecast.append(pred)
                        last_features[0] = pred
                        last_features[1] = (last_features[1] * 4 + pred) / 5
                        last_features[2] = (last_features[2] * 9 + pred) / 10
                        last_features[3] = (last_features[3] * 19 + pred) / 20
                
                st.success("✅ Model trained")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("1 Week", f"${ml_forecast[6]:.2f}",
                             f"{((ml_forecast[6] - current_price) / current_price * 100):+.1f}%")
                with col2:
                    st.metric("2 Weeks", f"${ml_forecast[13]:.2f}",
                             f"{((ml_forecast[13] - current_price) / current_price * 100):+.1f}%")
                with col3:
                    st.metric("1 Month", f"${ml_forecast[29]:.2f}",
                             f"{((ml_forecast[29] - current_price) / current_price * 100):+.1f}%")
                
                fig_ml = create_forecast_chart(symbol, prices, ml_forecast, "ML Forecast")
                if fig_ml:
                    st.plotly_chart(fig_ml, use_container_width=True)
            
            # TAB 4: Fundamental
            with tab4:
                st.subheader("💰 Fundamental")
                
                pe = info.get('trailingPE', None)
                peg = info.get('pegRatio', None)
                eps_growth = info.get('earningsGrowth', 0) * 100 if info.get('earningsGrowth') else None
                profit_margin = info.get('profitMargins', 0) * 100 if info.get('profitMargins') else None
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("P/E Ratio", f"{pe:.2f}" if pe else "N/A")
                    st.metric("EPS Growth", f"{eps_growth:.1f}%" if eps_growth else "N/A")
                with col2:
                    st.metric("PEG Ratio", f"{peg:.2f}" if peg else "N/A")
                    st.metric("Profit Margin", f"{profit_margin:.1f}%" if profit_margin else "N/A")
                
                score = 0
                if pe and pe < 20:
                    score += 1
                if peg and peg < 1:
                    score += 2
                if eps_growth and eps_growth > 10:
                    score += 1
                if profit_margin and profit_margin > 15:
                    score += 1
                
                st.markdown("---")
                if score >= 4:
                    st.success("🌟 UNDERVALUED")
                elif score >= 2:
                    st.success("✅ FAIRLY VALUED")
                else:
                    st.warning("⚠️ OVERVALUED")
        
        except Exception as e:
            st.error(f"Error: {str(e)}")

"""
Utility Functions for SharkFin
All helper functions, indicators, charting, news, etc.
"""

import yfinance as yf
import pandas as pd
import numpy as np
import feedparser
from datetime import datetime, timedelta
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ============================================================================
# STOCK SYMBOL MANAGEMENT
# ============================================================================

def get_sp500_symbols():
    """Get S&P 500 symbols from Wikipedia with fallback"""
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        tables = pd.read_html(url, header=0, storage_options={'User-Agent': headers['User-Agent']})
        df = tables[0]
        symbols = df['Symbol'].tolist()
        symbols = [s.replace('.', '-') for s in symbols]
        print(f"✅ Loaded {len(symbols)} S&P 500 symbols")
        return symbols
    except Exception as e:
        print(f"⚠️ Using fallback S&P 500 list")
        return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B', 'LLY', 'V',
                'UNH', 'XOM', 'JPM', 'JNJ', 'WMT', 'MA', 'PG', 'AVGO', 'HD', 'CVX',
                'MRK', 'ABBV', 'KO', 'COST', 'PEP', 'ADBE', 'MCD', 'CSCO', 'ACN', 'TMO',
                'LIN', 'NFLX', 'ABT', 'CRM', 'ORCL', 'AMD', 'NKE', 'DIS', 'TXN', 'CMCSA',
                'INTC', 'VZ', 'DHR', 'WFC', 'PM', 'NEE', 'QCOM', 'BMY', 'UNP', 'RTX',
                'HON', 'UPS', 'SPGI', 'BA', 'LOW', 'AMGN', 'IBM', 'CAT', 'GE', 'DE',
                'ELV', 'SCHW', 'BLK', 'PLD', 'GS', 'MDT', 'AXP', 'SYK', 'BKNG', 'GILD',
                'ADP', 'TJX', 'VRTX', 'MMC', 'MDLZ', 'REGN', 'AMT', 'CI', 'C', 'ADI',
                'ISRG', 'LRCX', 'CVS', 'MO', 'PGR', 'SO', 'ZTS', 'CB', 'NOW', 'TMUS',
                'DUK', 'SLB', 'BDX', 'NOC', 'CME', 'PYPL', 'ETN', 'ITW', 'MMM', 'PNC']

def get_nasdaq100_symbols():
    """Get NASDAQ-100 symbols from Wikipedia with fallback"""
    try:
        url = 'https://en.wikipedia.org/wiki/NASDAQ-100'
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        tables = pd.read_html(url, header=0, storage_options={'User-Agent': headers['User-Agent']})
        df = tables[4]
        symbols = df['Ticker'].tolist()
        print(f"✅ Loaded {len(symbols)} NASDAQ-100 symbols")
        return symbols
    except:
        print(f"⚠️ Using fallback NASDAQ-100 list")
        return ['AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'NVDA', 'META', 'TSLA', 'AVGO', 'COST',
                'NFLX', 'AMD', 'PEP', 'LIN', 'CSCO', 'ADBE', 'TMUS', 'TXN', 'QCOM', 'AMGN',
                'INTU', 'AMAT', 'HON', 'ISRG', 'CMCSA', 'BKNG', 'VRTX', 'PDD', 'ADP', 'SBUX',
                'GILD', 'ADI', 'MU', 'REGN', 'LRCX', 'PANW', 'PYPL', 'KLAC', 'MDLZ', 'SNPS']

def get_all_symbols():
    """Get all tracked symbols"""
    sp500 = get_sp500_symbols()
    nasdaq = get_nasdaq100_symbols()
    popular = ['PLTR', 'COIN', 'SNOW', 'ABNB', 'UBER', 'LYFT', 'RIVN', 'LCID', 
               'SOFI', 'HOOD', 'RBLX', 'U', 'PINS', 'SNAP', 'DOCU', 'ZM']
    all_symbols = list(set(sp500 + nasdaq + popular))
    return sorted(all_symbols)

def search_stock_symbol(query):
    """Search for stock symbols"""
    query = query.upper().strip()
    if not query:
        return []
    all_symbols = get_all_symbols()
    matches = [s for s in all_symbols if query in s]
    return matches[:20]

# ============================================================================
# TECHNICAL INDICATORS
# ============================================================================

def calculate_rsi(prices, period=14):
    """Calculate RSI"""
    if len(prices) < period + 1:
        return 50
    
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD"""
    if len(prices) < slow:
        return 0, 0, 0
    
    prices_series = pd.Series(prices)
    ema_fast = prices_series.ewm(span=fast, adjust=False).mean()
    ema_slow = prices_series.ewm(span=slow, adjust=False).mean()
    
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    
    return macd_line.iloc[-1], signal_line.iloc[-1], histogram.iloc[-1]

def calculate_bollinger_bands(prices, period=20, std_dev=2):
    """Calculate Bollinger Bands"""
    if len(prices) < period:
        return prices[-1], prices[-1], prices[-1]
    
    sma = sum(prices[-period:]) / period
    std = np.std(prices[-period:])
    
    upper_band = sma + (std_dev * std)
    lower_band = sma - (std_dev * std)
    
    return upper_band, sma, lower_band

# ============================================================================
# CHARTING
# ============================================================================

def create_candlestick_chart(symbol, hist, timeframe="3mo"):
    """Create candlestick chart"""
    try:
        fig = go.Figure(data=[go.Candlestick(
            x=hist.index,
            open=hist['Open'],
            high=hist['High'],
            low=hist['Low'],
            close=hist['Close'],
            increasing_line_color='#00ff88',
            decreasing_line_color='#ff4444',
            increasing_fillcolor='#00ff88',
            decreasing_fillcolor='#ff4444'
        )])
        
        fig.update_layout(
            title=dict(text=f'{symbol} - {timeframe}', font=dict(color='white', size=18)),
            yaxis_title='Price ($)',
            template='plotly_dark',
            height=450,
            xaxis_rangeslider_visible=False,
            paper_bgcolor='#1a1a1a',
            plot_bgcolor='#1a1a1a',
            font=dict(color='white'),
            xaxis=dict(gridcolor='#2a2a2a', showgrid=True),
            yaxis=dict(gridcolor='#2a2a2a', showgrid=True),
            margin=dict(l=50, r=50, t=60, b=50)
        )
        
        return fig
    except:
        return None

def create_forecast_chart(symbol, historical_prices, forecast_prices, model_name):
    """Create forecast chart with historical + predicted prices"""
    try:
        fig = go.Figure()
        
        # Historical prices
        hist_x = list(range(len(historical_prices[-60:])))
        fig.add_trace(go.Scatter(
            x=hist_x,
            y=historical_prices[-60:],
            mode='lines',
            name='Historical',
            line=dict(color='#00d4ff', width=2.5)
        ))
        
        # Forecast prices
        forecast_x = list(range(len(historical_prices[-60:]), len(historical_prices[-60:]) + len(forecast_prices)))
        fig.add_trace(go.Scatter(
            x=forecast_x,
            y=forecast_prices,
            mode='lines',
            name='Forecast',
            line=dict(color='#ff8800', width=2.5, dash='dash')
        ))
        
        fig.update_layout(
            title=dict(text=f'{symbol} - {model_name}', font=dict(color='white', size=16)),
            yaxis_title='Price ($)',
            xaxis_title='Days',
            template='plotly_dark',
            height=400,
            paper_bgcolor='#1a1a1a',
            plot_bgcolor='#1a1a1a',
            font=dict(color='white'),
            xaxis=dict(gridcolor='#2a2a2a', showgrid=True),
            yaxis=dict(gridcolor='#2a2a2a', showgrid=True),
            legend=dict(bgcolor='#2a2a2a', bordercolor='#00d4ff', borderwidth=1),
            margin=dict(l=50, r=50, t=60, b=50)
        )
        
        return fig
    except:
        return None

# ============================================================================
# NEWS FUNCTIONS
# ============================================================================

def get_news_from_yahoo(query, count):
    """Fetch news from Yahoo Finance RSS"""
    try:
        query_lower = query.lower()
        filter_keywords = None
        
        if 'technology stocks' in query_lower:
            url = 'https://finance.yahoo.com/rss/headline?s=^IXIC'
        elif 'healthcare' in query_lower:
            url = 'https://finance.yahoo.com/news/rssindex'
            filter_keywords = ['healthcare', 'pharma', 'biotech', 'medical', 'drug', 'hospital']
        elif 'energy' in query_lower:
            url = 'https://finance.yahoo.com/news/rssindex'
            filter_keywords = ['energy', 'oil', 'gas', 'renewable', 'solar', 'wind']
        elif 'banking' in query_lower or 'finance stocks' in query_lower:
            url = 'https://finance.yahoo.com/news/rssindex'
            filter_keywords = ['bank', 'banking', 'financial', 'fed', 'interest']
        elif 'mergers' in query_lower:
            url = 'https://finance.yahoo.com/news/rssindex'
            filter_keywords = ['merger', 'acquisition', 'deal', 'takeover', 'buyout']
        elif 'food' in query_lower:
            url = 'https://finance.yahoo.com/news/rssindex'
            filter_keywords = ['food', 'beverage', 'restaurant', 'consumer']
        elif 'financial markets' in query_lower or query_lower == 'all':
            url = 'https://finance.yahoo.com/news/rssindex'
        else:
            symbol = query.upper().replace(' STOCK', '').strip().split()[0]
            url = f'https://finance.yahoo.com/rss/headline?s={symbol}'
        
        feed = feedparser.parse(url)
        cutoff_date = datetime.now() - timedelta(days=7)
        
        articles = []
        for entry in feed.entries:
            try:
                pub_date = datetime(*entry.published_parsed[:6])
                if pub_date < cutoff_date:
                    continue
            except:
                pass
            
            title = entry.get('title', '').lower()
            summary = entry.get('summary', '').lower()
            
            if filter_keywords:
                if not any(kw in title or kw in summary for kw in filter_keywords):
                    continue
            
            articles.append({
                'title': entry.get('title', 'No title'),
                'description': entry.get('summary', ''),
                'source': {'name': 'Yahoo Finance'},
                'publishedAt': entry.get('published', datetime.now().isoformat())
            })
            
            if len(articles) >= count * 2:
                break
        
        return articles[:count]
    except:
        return []

def calculate_article_relevance(article, query):
    """ML relevance scoring"""
    try:
        article_text = f"{article['title']} {article.get('description', '')}"
        vectorizer = TfidfVectorizer(stop_words='english', max_features=100)
        
        try:
            vectors = vectorizer.fit_transform([query.lower(), article_text.lower()])
            similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
        except:
            similarity = 0.0
        
        score = similarity
        
        # Boost for query words in title
        for word in query.lower().split():
            if len(word) > 3 and word in article['title'].lower():
                score += 0.2
        
        # Boost for important keywords
        important = ['earnings', 'billion', 'merger', 'breakthrough', 'deal']
        for kw in important:
            if kw in article['title'].lower():
                score += 0.1
        
        # Recency boost
        try:
            pub_str = article.get('publishedAt', '')
            if pub_str:
                pub_date = datetime.fromisoformat(pub_str.replace('Z', '+00:00'))
                days_old = (datetime.now() - pub_date.replace(tzinfo=None)).days
                if days_old <= 1:
                    score += 0.3
                elif days_old <= 3:
                    score += 0.2
        except:
            pass
        
        return score
    except:
        return 0.5

def search_news_google(query, count):
    """Google News RSS backup"""
    try:
        encoded = query.replace(' ', '+')
        url = f'https://news.google.com/rss/search?q={encoded}+stock&hl=en-US&gl=US&ceid=US:en'
        
        feed = feedparser.parse(url)
        articles = []
        
        for entry in feed.entries[:count * 3]:
            article = {
                'title': entry.get('title', 'No title'),
                'description': entry.get('summary', ''),
                'source': {'name': 'Google News'},
                'publishedAt': entry.get('published', datetime.now().isoformat())
            }
            article['relevance_score'] = calculate_article_relevance(article, query)
            articles.append(article)
        
        articles = sorted(articles, key=lambda x: x['relevance_score'], reverse=True)
        return articles[:count]
    except:
        return []

def get_news_from_api(query, count, cache):
    """Main news function with caching"""
    if query in cache:
        cached_time, cached_data = cache[query]
        if (datetime.now() - cached_time).seconds < 1800:
            return cached_data
    
    articles = get_news_from_yahoo(query, count)
    
    if len(articles) < 5 and query.lower() not in ['all', 'financial markets economy stocks']:
        google_articles = search_news_google(query, count)
        articles.extend(google_articles)
        
        seen = set()
        unique = []
        for a in articles:
            title = a['title'].lower()
            if title not in seen:
                seen.add(title)
                unique.append(a)
        articles = unique[:count]
    
    if articles:
        cache[query] = (datetime.now(), articles)
    
    return articles

def format_time_ago(date_str):
    """Format date as time ago"""
    try:
        if 'T' in date_str:
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            date_obj = datetime.strptime(date_str[:19], '%a, %d %b %Y %H:%M:%S')
        
        now = datetime.now()
        diff = now - date_obj.replace(tzinfo=None)
        
        if diff.days == 0:
            if diff.seconds < 3600:
                return f"{diff.seconds // 60}m ago"
            else:
                return f"{diff.seconds // 3600}h ago"
        elif diff.days == 1:
            return "Yesterday"
        elif diff.days < 7:
            return f"{diff.days}d ago"
        else:
            return date_obj.strftime("%b %d, %Y")
    except:
        return date_str[:10] if date_str else "Recent"

def generate_article_summary(title, description):
    """Generate brief summary of article"""
    if description and len(description) > 20:
        # Clean up description
        summary = description.replace('<![CDATA[', '').replace(']]>', '')
        summary = summary.replace('<p>', '').replace('</p>', '')
        summary = summary.replace('<br>', ' ').replace('<br/>', ' ')
        
        # Truncate to reasonable length
        if len(summary) > 150:
            summary = summary[:147] + "..."
        
        return summary
    else:
        # Generate from title
        words = title.split()
        if len(words) > 8:
            return ' '.join(words[:8]) + "..."
        return title

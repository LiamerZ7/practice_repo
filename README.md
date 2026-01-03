# Revolut Trading Assistant

A user-friendly day trading app that helps you find and analyze cryptocurrencies and stocks available on Revolut. Get clear buy/sell signals based on technical analysis.

## Features

- **30+ Revolut Cryptocurrencies** - All major cryptos available on Revolut with real-time prices
- **55+ Revolut Stocks** - Popular US stocks and ETFs from tech, finance, healthcare, and more
- **Technical Analysis** - RSI, MACD, Moving Averages, Bollinger Bands
- **Clear Buy/Sell Signals** - Easy-to-understand recommendations (Strong Buy, Buy, Hold, Sell, Strong Sell)
- **Asset Screener** - Find oversold/overbought assets or those with strong signals
- **Portfolio Tracker** - Track your holdings and P&L
- **Watchlist** - Monitor assets you're interested in
- **Dark Mode UI** - Clean, modern interface optimized for trading

## Screenshots

The dashboard shows:
- Market overview (S&P 500, Dow Jones, NASDAQ, VIX)
- Top trading opportunities with signal scores
- What to buy and what to sell at a glance

## Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd practice_repo

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running the App

```bash
python app.py
```

Open your browser and navigate to: **http://localhost:5000**

## How to Use

### Dashboard
The main dashboard shows:
- **Market Overview**: Major indices to understand market conditions
- **Top Trading Opportunities**: Assets with the strongest buy signals
- **Consider Buying**: Assets showing bullish indicators
- **Consider Selling**: Assets showing bearish indicators

### Trading Signals
View all analyzed assets with:
- Current price and 24h change
- RSI (Relative Strength Index)
- Signal recommendation (Strong Buy to Strong Sell)
- Signal score (0-100)

Filter by:
- All assets
- Buy signals only
- Sell signals only
- Crypto only
- Stocks only

### Asset Screener
Find assets matching specific criteria:
- **Oversold (RSI < 30)** - Potential bounce candidates
- **Overbought (RSI > 70)** - Potential pullback candidates
- **Strong Buy Signals** - Multiple bullish indicators
- **Strong Sell Signals** - Multiple bearish indicators

### Detailed Analysis
Click any asset to see:
- Current price and changes (1d, 7d, 30d)
- RSI with status (Overbought/Oversold/Neutral)
- MACD histogram and trend
- Moving averages (SMA 20, SMA 50, EMA 12, EMA 26)
- Bollinger Band position
- AI-generated analysis summary

### Portfolio Tracker
- Add your holdings with buy price
- See current value and P&L
- Track overall portfolio performance

### Watchlist
- Add assets to monitor
- Quick access to detailed analysis

## Technical Indicators Explained

| Indicator | What it means |
|-----------|---------------|
| **RSI < 30** | Oversold - potential buying opportunity |
| **RSI > 70** | Overbought - caution, potential pullback |
| **MACD Bullish** | Momentum is positive |
| **MACD Bearish** | Momentum is negative |
| **Price > SMA 20** | Short-term uptrend |
| **SMA 20 > SMA 50** | Medium-term uptrend (Golden Cross territory) |
| **BB Position < 20%** | Near lower band - potential bounce |
| **BB Position > 80%** | Near upper band - potential resistance |

## Signal Score

The signal score (0-100) combines multiple indicators:
- **80-100**: Strong Buy
- **60-79**: Buy
- **45-59**: Hold
- **40-44**: Sell
- **0-39**: Strong Sell

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/crypto/prices` | All crypto prices |
| `GET /api/crypto/<symbol>/analyze` | Crypto analysis |
| `GET /api/stock/<symbol>/analyze` | Stock analysis |
| `GET /api/signals` | All trading signals |
| `GET /api/screener?criteria=<type>` | Screen assets |
| `GET /api/market/overview` | Market indices |
| `GET/POST/DELETE /api/portfolio` | Portfolio management |
| `GET/POST/DELETE /api/watchlist` | Watchlist management |

## Disclaimer

This app is for **educational and informational purposes only**. It is not financial advice. Always do your own research before making investment decisions. Past performance does not guarantee future results. Trading cryptocurrencies and stocks involves significant risk.

## Tech Stack

- **Backend**: Python, Flask
- **Data**: Yahoo Finance (stocks), CoinGecko (crypto)
- **Analysis**: Pandas, NumPy
- **Frontend**: HTML, CSS, JavaScript

## License

MIT License

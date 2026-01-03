"""
Data Fetcher Module
Fetches real-time and historical data for stocks and cryptocurrencies
"""

import time
import requests
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from config import REVOLUT_CRYPTOS, REVOLUT_STOCKS, API_SETTINGS

# Cache to reduce API calls
_cache = {}
_cache_timestamps = {}


def get_cached(key: str, timeout: int = None):
    """Get cached data if still valid"""
    if timeout is None:
        timeout = API_SETTINGS["cache_timeout"]
    if key in _cache and key in _cache_timestamps:
        if time.time() - _cache_timestamps[key] < timeout:
            return _cache[key]
    return None


def set_cache(key: str, data):
    """Store data in cache"""
    _cache[key] = data
    _cache_timestamps[key] = time.time()


def fetch_stock_data(symbol: str, period: str = "3mo", interval: str = "1d") -> pd.DataFrame:
    """
    Fetch stock data from Yahoo Finance
    Returns DataFrame with OHLCV data
    """
    cache_key = f"stock_{symbol}_{period}_{interval}"
    cached = get_cached(cache_key, timeout=300)  # 5 min cache for historical data
    if cached is not None:
        return cached

    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        if not df.empty:
            set_cache(cache_key, df)
        return df
    except Exception as e:
        print(f"Error fetching stock data for {symbol}: {e}")
        return pd.DataFrame()


def fetch_stock_info(symbol: str) -> dict:
    """Fetch current stock info and quote"""
    cache_key = f"stock_info_{symbol}"
    cached = get_cached(cache_key, timeout=60)
    if cached is not None:
        return cached

    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        result = {
            "symbol": symbol,
            "name": info.get("shortName", symbol),
            "price": info.get("regularMarketPrice", info.get("currentPrice", 0)),
            "change": info.get("regularMarketChange", 0),
            "change_percent": info.get("regularMarketChangePercent", 0),
            "volume": info.get("regularMarketVolume", 0),
            "market_cap": info.get("marketCap", 0),
            "day_high": info.get("dayHigh", 0),
            "day_low": info.get("dayLow", 0),
            "52_week_high": info.get("fiftyTwoWeekHigh", 0),
            "52_week_low": info.get("fiftyTwoWeekLow", 0),
            "pe_ratio": info.get("trailingPE", 0),
            "sector": info.get("sector", "N/A"),
        }
        set_cache(cache_key, result)
        return result
    except Exception as e:
        print(f"Error fetching stock info for {symbol}: {e}")
        return {"symbol": symbol, "error": str(e)}


def fetch_crypto_prices() -> dict:
    """Fetch current prices for all Revolut cryptos from CoinGecko"""
    cache_key = "crypto_prices_all"
    cached = get_cached(cache_key, timeout=30)
    if cached is not None:
        return cached

    try:
        ids = ",".join([c["coingecko_id"] for c in REVOLUT_CRYPTOS])
        url = f"{API_SETTINGS['coingecko_base_url']}/simple/price"
        params = {
            "ids": ids,
            "vs_currencies": "usd",
            "include_24hr_vol": "true",
            "include_24hr_change": "true",
            "include_market_cap": "true",
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        result = {}
        for crypto in REVOLUT_CRYPTOS:
            cg_id = crypto["coingecko_id"]
            if cg_id in data:
                result[crypto["symbol"]] = {
                    "symbol": crypto["symbol"],
                    "name": crypto["name"],
                    "price": data[cg_id].get("usd", 0),
                    "change_24h": data[cg_id].get("usd_24h_change", 0),
                    "volume_24h": data[cg_id].get("usd_24h_vol", 0),
                    "market_cap": data[cg_id].get("usd_market_cap", 0),
                }

        set_cache(cache_key, result)
        return result
    except Exception as e:
        print(f"Error fetching crypto prices: {e}")
        return {}


def fetch_crypto_history(coingecko_id: str, days: int = 90) -> pd.DataFrame:
    """Fetch historical data for a cryptocurrency"""
    cache_key = f"crypto_history_{coingecko_id}_{days}"
    cached = get_cached(cache_key, timeout=300)
    if cached is not None:
        return cached

    try:
        url = f"{API_SETTINGS['coingecko_base_url']}/coins/{coingecko_id}/market_chart"
        params = {"vs_currency": "usd", "days": days}

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Convert to DataFrame
        prices = data.get("prices", [])
        volumes = data.get("total_volumes", [])

        if not prices:
            return pd.DataFrame()

        df = pd.DataFrame(prices, columns=["timestamp", "Close"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)

        # Add volume if available
        if volumes:
            vol_df = pd.DataFrame(volumes, columns=["timestamp", "Volume"])
            vol_df["timestamp"] = pd.to_datetime(vol_df["timestamp"], unit="ms")
            vol_df.set_index("timestamp", inplace=True)
            df = df.join(vol_df["Volume"], how="left")

        # Add High/Low as approximations (for crypto, we use close as proxy)
        df["High"] = df["Close"]
        df["Low"] = df["Close"]
        df["Open"] = df["Close"].shift(1)

        set_cache(cache_key, df)
        return df
    except Exception as e:
        print(f"Error fetching crypto history for {coingecko_id}: {e}")
        return pd.DataFrame()


def get_crypto_by_symbol(symbol: str) -> dict:
    """Get crypto config by symbol"""
    for crypto in REVOLUT_CRYPTOS:
        if crypto["symbol"].upper() == symbol.upper():
            return crypto
    return None


def get_stock_by_symbol(symbol: str) -> dict:
    """Get stock config by symbol"""
    for stock in REVOLUT_STOCKS:
        if stock["symbol"].upper() == symbol.upper():
            return stock
    return None


def fetch_market_overview() -> dict:
    """Fetch overall market indicators"""
    try:
        # Major indices
        indices = {
            "^GSPC": "S&P 500",
            "^DJI": "Dow Jones",
            "^IXIC": "NASDAQ",
            "^VIX": "VIX (Fear Index)",
        }

        market_data = {}
        for symbol, name in indices.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                if len(hist) >= 2:
                    current = hist["Close"].iloc[-1]
                    previous = hist["Close"].iloc[-2]
                    change = ((current / previous) - 1) * 100
                    market_data[symbol] = {
                        "name": name,
                        "price": round(current, 2),
                        "change": round(change, 2),
                    }
            except:
                pass

        return market_data
    except Exception as e:
        print(f"Error fetching market overview: {e}")
        return {}


def get_trending_assets(asset_type: str = "all", limit: int = 10) -> list:
    """Get top trending assets by volume or price change"""
    trending = []

    if asset_type in ["all", "crypto"]:
        prices = fetch_crypto_prices()
        crypto_list = [
            {**v, "type": "crypto"}
            for v in prices.values()
        ]
        trending.extend(crypto_list)

    if asset_type in ["all", "stock"]:
        for stock in REVOLUT_STOCKS[:20]:  # Limit initial fetch
            info = fetch_stock_info(stock["symbol"])
            if "error" not in info:
                info["type"] = "stock"
                trending.append(info)
            time.sleep(0.1)  # Rate limiting

    # Sort by absolute change percentage
    trending.sort(
        key=lambda x: abs(x.get("change_24h", x.get("change_percent", 0))),
        reverse=True
    )

    return trending[:limit]

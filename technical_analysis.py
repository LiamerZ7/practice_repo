"""
Technical Analysis Module for Day Trading
Provides indicators and signals for buy/sell decisions
"""

import numpy as np
import pandas as pd
from config import TA_SETTINGS, SIGNAL_THRESHOLDS


def calculate_sma(prices: pd.Series, period: int) -> pd.Series:
    """Calculate Simple Moving Average"""
    return prices.rolling(window=period).mean()


def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average"""
    return prices.ewm(span=period, adjust=False).mean()


def calculate_rsi(prices: pd.Series, period: int = None) -> pd.Series:
    """
    Calculate Relative Strength Index (RSI)
    RSI > 70 = Overbought (potential sell)
    RSI < 30 = Oversold (potential buy)
    """
    if period is None:
        period = TA_SETTINGS["rsi_period"]

    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(prices: pd.Series) -> dict:
    """
    Calculate MACD (Moving Average Convergence Divergence)
    Returns MACD line, Signal line, and Histogram
    """
    fast = TA_SETTINGS["macd_fast"]
    slow = TA_SETTINGS["macd_slow"]
    signal = TA_SETTINGS["macd_signal"]

    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)

    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal)
    histogram = macd_line - signal_line

    return {
        "macd": macd_line,
        "signal": signal_line,
        "histogram": histogram
    }


def calculate_bollinger_bands(prices: pd.Series) -> dict:
    """
    Calculate Bollinger Bands
    Price near upper band = potential overbought
    Price near lower band = potential oversold
    """
    period = TA_SETTINGS["bollinger_period"]
    std_dev = TA_SETTINGS["bollinger_std"]

    middle = calculate_sma(prices, period)
    std = prices.rolling(window=period).std()

    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)

    return {
        "upper": upper,
        "middle": middle,
        "lower": lower,
        "bandwidth": (upper - lower) / middle * 100
    }


def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series,
                         k_period: int = 14, d_period: int = 3) -> dict:
    """
    Calculate Stochastic Oscillator
    %K > 80 = Overbought
    %K < 20 = Oversold
    """
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()

    k = 100 * (close - lowest_low) / (highest_high - lowest_low)
    d = k.rolling(window=d_period).mean()

    return {"k": k, "d": d}


def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series,
                  period: int = 14) -> pd.Series:
    """
    Calculate Average True Range (ATR)
    Measures volatility
    """
    high_low = high - low
    high_close = abs(high - close.shift())
    low_close = abs(low - close.shift())

    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()

    return atr


def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """
    Calculate On-Balance Volume (OBV)
    Measures buying/selling pressure
    """
    obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
    return obv


def calculate_vwap(high: pd.Series, low: pd.Series, close: pd.Series,
                   volume: pd.Series) -> pd.Series:
    """
    Calculate Volume Weighted Average Price (VWAP)
    Used for intraday trading decisions
    """
    typical_price = (high + low + close) / 3
    vwap = (typical_price * volume).cumsum() / volume.cumsum()
    return vwap


def get_signal_strength(score: float) -> dict:
    """Convert numerical score to signal recommendation"""
    if score >= SIGNAL_THRESHOLDS["strong_buy"]:
        return {"signal": "STRONG BUY", "color": "#00ff00", "icon": "🚀"}
    elif score >= SIGNAL_THRESHOLDS["buy"]:
        return {"signal": "BUY", "color": "#90EE90", "icon": "📈"}
    elif score >= SIGNAL_THRESHOLDS["neutral_high"]:
        return {"signal": "HOLD", "color": "#FFD700", "icon": "⏸️"}
    elif score >= SIGNAL_THRESHOLDS["neutral_low"]:
        return {"signal": "HOLD", "color": "#FFD700", "icon": "⏸️"}
    elif score >= SIGNAL_THRESHOLDS["sell"]:
        return {"signal": "SELL", "color": "#FFA07A", "icon": "📉"}
    else:
        return {"signal": "STRONG SELL", "color": "#FF0000", "icon": "⚠️"}


def analyze_asset(df: pd.DataFrame) -> dict:
    """
    Perform comprehensive technical analysis on an asset
    Returns all indicators and a trading signal
    """
    if df is None or len(df) < 50:
        return None

    close = df["Close"]
    high = df.get("High", close)
    low = df.get("Low", close)
    volume = df.get("Volume", pd.Series([0] * len(close)))

    # Calculate all indicators
    rsi = calculate_rsi(close)
    macd_data = calculate_macd(close)
    bollinger = calculate_bollinger_bands(close)
    sma_short = calculate_sma(close, TA_SETTINGS["sma_short"])
    sma_long = calculate_sma(close, TA_SETTINGS["sma_long"])
    ema_short = calculate_ema(close, TA_SETTINGS["ema_short"])
    ema_long = calculate_ema(close, TA_SETTINGS["ema_long"])

    # Get latest values
    current_price = close.iloc[-1]
    current_rsi = rsi.iloc[-1]
    current_macd = macd_data["macd"].iloc[-1]
    current_signal = macd_data["signal"].iloc[-1]
    current_histogram = macd_data["histogram"].iloc[-1]

    # Calculate signal score (0-100)
    score = 50  # Start neutral

    # RSI contribution (-20 to +20)
    if current_rsi < 30:
        score += 20  # Oversold = bullish
    elif current_rsi < 40:
        score += 10
    elif current_rsi > 70:
        score -= 20  # Overbought = bearish
    elif current_rsi > 60:
        score -= 10

    # MACD contribution (-15 to +15)
    if current_macd > current_signal and current_histogram > 0:
        score += 15  # Bullish crossover
    elif current_macd < current_signal and current_histogram < 0:
        score -= 15  # Bearish crossover

    # Moving Average contribution (-15 to +15)
    if sma_short.iloc[-1] > sma_long.iloc[-1]:
        score += 10  # Golden cross territory
        if current_price > sma_short.iloc[-1]:
            score += 5  # Price above short MA
    else:
        score -= 10  # Death cross territory
        if current_price < sma_short.iloc[-1]:
            score -= 5  # Price below short MA

    # Bollinger Bands contribution (-10 to +10)
    bb_position = (current_price - bollinger["lower"].iloc[-1]) / \
                  (bollinger["upper"].iloc[-1] - bollinger["lower"].iloc[-1])
    if bb_position < 0.2:
        score += 10  # Near lower band = potential bounce
    elif bb_position > 0.8:
        score -= 10  # Near upper band = potential reversal

    # Trend analysis
    price_change_1d = ((current_price / close.iloc[-2]) - 1) * 100 if len(close) > 1 else 0
    price_change_7d = ((current_price / close.iloc[-7]) - 1) * 100 if len(close) > 7 else 0
    price_change_30d = ((current_price / close.iloc[-30]) - 1) * 100 if len(close) > 30 else 0

    # Ensure score is within bounds
    score = max(0, min(100, score))

    signal_info = get_signal_strength(score)

    return {
        "current_price": round(current_price, 4),
        "indicators": {
            "rsi": round(current_rsi, 2),
            "rsi_status": "Overbought" if current_rsi > 70 else "Oversold" if current_rsi < 30 else "Neutral",
            "macd": round(current_macd, 4),
            "macd_signal": round(current_signal, 4),
            "macd_histogram": round(current_histogram, 4),
            "macd_status": "Bullish" if current_histogram > 0 else "Bearish",
            "sma_20": round(sma_short.iloc[-1], 4),
            "sma_50": round(sma_long.iloc[-1], 4),
            "ema_12": round(ema_short.iloc[-1], 4),
            "ema_26": round(ema_long.iloc[-1], 4),
            "bb_upper": round(bollinger["upper"].iloc[-1], 4),
            "bb_middle": round(bollinger["middle"].iloc[-1], 4),
            "bb_lower": round(bollinger["lower"].iloc[-1], 4),
            "bb_position": round(bb_position * 100, 2),
        },
        "price_changes": {
            "1d": round(price_change_1d, 2),
            "7d": round(price_change_7d, 2),
            "30d": round(price_change_30d, 2),
        },
        "signal_score": round(score, 2),
        "signal": signal_info["signal"],
        "signal_color": signal_info["color"],
        "signal_icon": signal_info["icon"],
        "analysis_summary": generate_analysis_summary(
            current_rsi, current_histogram, sma_short.iloc[-1],
            sma_long.iloc[-1], current_price, bb_position, score
        )
    }


def generate_analysis_summary(rsi, macd_hist, sma_short, sma_long,
                              price, bb_position, score) -> list:
    """Generate human-readable analysis points"""
    summary = []

    # RSI insight
    if rsi > 70:
        summary.append("⚠️ RSI indicates overbought conditions - caution advised")
    elif rsi < 30:
        summary.append("💡 RSI shows oversold conditions - potential buying opportunity")
    else:
        summary.append(f"📊 RSI at {rsi:.1f} - neutral momentum")

    # MACD insight
    if macd_hist > 0:
        summary.append("📈 MACD shows bullish momentum")
    else:
        summary.append("📉 MACD shows bearish momentum")

    # Moving Average insight
    if sma_short > sma_long:
        if price > sma_short:
            summary.append("✅ Strong uptrend - price above both moving averages")
        else:
            summary.append("🔄 Uptrend but price pulling back to support")
    else:
        if price < sma_short:
            summary.append("⚠️ Downtrend - price below moving averages")
        else:
            summary.append("🔄 Downtrend but price attempting recovery")

    # Bollinger Bands insight
    if bb_position < 0.2:
        summary.append("💰 Price near lower Bollinger Band - potential bounce zone")
    elif bb_position > 0.8:
        summary.append("🎯 Price near upper Bollinger Band - potential resistance")

    return summary

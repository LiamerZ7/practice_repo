"""
Configuration settings for the Revolut Trading App
"""

# Revolut-supported cryptocurrencies (as of 2024)
REVOLUT_CRYPTOS = [
    {"symbol": "BTC", "name": "Bitcoin", "coingecko_id": "bitcoin"},
    {"symbol": "ETH", "name": "Ethereum", "coingecko_id": "ethereum"},
    {"symbol": "XRP", "name": "Ripple", "coingecko_id": "ripple"},
    {"symbol": "LTC", "name": "Litecoin", "coingecko_id": "litecoin"},
    {"symbol": "BCH", "name": "Bitcoin Cash", "coingecko_id": "bitcoin-cash"},
    {"symbol": "XLM", "name": "Stellar", "coingecko_id": "stellar"},
    {"symbol": "EOS", "name": "EOS", "coingecko_id": "eos"},
    {"symbol": "OMG", "name": "OMG Network", "coingecko_id": "omisego"},
    {"symbol": "DOGE", "name": "Dogecoin", "coingecko_id": "dogecoin"},
    {"symbol": "ADA", "name": "Cardano", "coingecko_id": "cardano"},
    {"symbol": "DOT", "name": "Polkadot", "coingecko_id": "polkadot"},
    {"symbol": "UNI", "name": "Uniswap", "coingecko_id": "uniswap"},
    {"symbol": "LINK", "name": "Chainlink", "coingecko_id": "chainlink"},
    {"symbol": "SOL", "name": "Solana", "coingecko_id": "solana"},
    {"symbol": "AVAX", "name": "Avalanche", "coingecko_id": "avalanche-2"},
    {"symbol": "MATIC", "name": "Polygon", "coingecko_id": "matic-network"},
    {"symbol": "SHIB", "name": "Shiba Inu", "coingecko_id": "shiba-inu"},
    {"symbol": "ATOM", "name": "Cosmos", "coingecko_id": "cosmos"},
    {"symbol": "ALGO", "name": "Algorand", "coingecko_id": "algorand"},
    {"symbol": "XTZ", "name": "Tezos", "coingecko_id": "tezos"},
    {"symbol": "AAVE", "name": "Aave", "coingecko_id": "aave"},
    {"symbol": "SAND", "name": "The Sandbox", "coingecko_id": "the-sandbox"},
    {"symbol": "MANA", "name": "Decentraland", "coingecko_id": "decentraland"},
    {"symbol": "APE", "name": "ApeCoin", "coingecko_id": "apecoin"},
    {"symbol": "CRV", "name": "Curve DAO", "coingecko_id": "curve-dao-token"},
    {"symbol": "ENS", "name": "Ethereum Name Service", "coingecko_id": "ethereum-name-service"},
    {"symbol": "LDO", "name": "Lido DAO", "coingecko_id": "lido-dao"},
    {"symbol": "NEAR", "name": "NEAR Protocol", "coingecko_id": "near"},
    {"symbol": "FTM", "name": "Fantom", "coingecko_id": "fantom"},
    {"symbol": "1INCH", "name": "1inch", "coingecko_id": "1inch"},
]

# Popular Revolut-supported stocks (major US stocks available on Revolut)
REVOLUT_STOCKS = [
    # Tech Giants
    {"symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology"},
    {"symbol": "MSFT", "name": "Microsoft Corporation", "sector": "Technology"},
    {"symbol": "GOOGL", "name": "Alphabet Inc.", "sector": "Technology"},
    {"symbol": "AMZN", "name": "Amazon.com Inc.", "sector": "Technology"},
    {"symbol": "META", "name": "Meta Platforms Inc.", "sector": "Technology"},
    {"symbol": "NVDA", "name": "NVIDIA Corporation", "sector": "Technology"},
    {"symbol": "TSLA", "name": "Tesla Inc.", "sector": "Automotive"},
    {"symbol": "AMD", "name": "Advanced Micro Devices", "sector": "Technology"},
    {"symbol": "INTC", "name": "Intel Corporation", "sector": "Technology"},
    {"symbol": "CRM", "name": "Salesforce Inc.", "sector": "Technology"},
    {"symbol": "ORCL", "name": "Oracle Corporation", "sector": "Technology"},
    {"symbol": "ADBE", "name": "Adobe Inc.", "sector": "Technology"},
    {"symbol": "NFLX", "name": "Netflix Inc.", "sector": "Entertainment"},
    {"symbol": "PYPL", "name": "PayPal Holdings", "sector": "Fintech"},
    {"symbol": "SQ", "name": "Block Inc.", "sector": "Fintech"},
    {"symbol": "SHOP", "name": "Shopify Inc.", "sector": "Technology"},
    {"symbol": "UBER", "name": "Uber Technologies", "sector": "Technology"},
    {"symbol": "LYFT", "name": "Lyft Inc.", "sector": "Technology"},
    {"symbol": "SNAP", "name": "Snap Inc.", "sector": "Technology"},
    {"symbol": "PINS", "name": "Pinterest Inc.", "sector": "Technology"},
    {"symbol": "TWLO", "name": "Twilio Inc.", "sector": "Technology"},
    {"symbol": "ZM", "name": "Zoom Video", "sector": "Technology"},
    {"symbol": "PLTR", "name": "Palantir Technologies", "sector": "Technology"},
    {"symbol": "COIN", "name": "Coinbase Global", "sector": "Fintech"},
    {"symbol": "HOOD", "name": "Robinhood Markets", "sector": "Fintech"},

    # Finance
    {"symbol": "JPM", "name": "JPMorgan Chase", "sector": "Finance"},
    {"symbol": "BAC", "name": "Bank of America", "sector": "Finance"},
    {"symbol": "WFC", "name": "Wells Fargo", "sector": "Finance"},
    {"symbol": "GS", "name": "Goldman Sachs", "sector": "Finance"},
    {"symbol": "MS", "name": "Morgan Stanley", "sector": "Finance"},
    {"symbol": "V", "name": "Visa Inc.", "sector": "Finance"},
    {"symbol": "MA", "name": "Mastercard Inc.", "sector": "Finance"},
    {"symbol": "AXP", "name": "American Express", "sector": "Finance"},

    # Healthcare
    {"symbol": "JNJ", "name": "Johnson & Johnson", "sector": "Healthcare"},
    {"symbol": "PFE", "name": "Pfizer Inc.", "sector": "Healthcare"},
    {"symbol": "UNH", "name": "UnitedHealth Group", "sector": "Healthcare"},
    {"symbol": "MRNA", "name": "Moderna Inc.", "sector": "Healthcare"},
    {"symbol": "ABBV", "name": "AbbVie Inc.", "sector": "Healthcare"},

    # Consumer
    {"symbol": "WMT", "name": "Walmart Inc.", "sector": "Retail"},
    {"symbol": "COST", "name": "Costco Wholesale", "sector": "Retail"},
    {"symbol": "TGT", "name": "Target Corporation", "sector": "Retail"},
    {"symbol": "HD", "name": "Home Depot", "sector": "Retail"},
    {"symbol": "NKE", "name": "Nike Inc.", "sector": "Consumer"},
    {"symbol": "SBUX", "name": "Starbucks Corporation", "sector": "Consumer"},
    {"symbol": "MCD", "name": "McDonald's Corporation", "sector": "Consumer"},
    {"symbol": "KO", "name": "Coca-Cola Company", "sector": "Consumer"},
    {"symbol": "PEP", "name": "PepsiCo Inc.", "sector": "Consumer"},
    {"symbol": "DIS", "name": "Walt Disney Company", "sector": "Entertainment"},

    # Energy
    {"symbol": "XOM", "name": "Exxon Mobil", "sector": "Energy"},
    {"symbol": "CVX", "name": "Chevron Corporation", "sector": "Energy"},

    # ETFs
    {"symbol": "SPY", "name": "SPDR S&P 500 ETF", "sector": "ETF"},
    {"symbol": "QQQ", "name": "Invesco QQQ Trust", "sector": "ETF"},
    {"symbol": "IWM", "name": "iShares Russell 2000", "sector": "ETF"},
    {"symbol": "VTI", "name": "Vanguard Total Stock Market", "sector": "ETF"},
    {"symbol": "ARKK", "name": "ARK Innovation ETF", "sector": "ETF"},
]

# Technical Analysis Settings
TA_SETTINGS = {
    "rsi_period": 14,
    "rsi_overbought": 70,
    "rsi_oversold": 30,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "sma_short": 20,
    "sma_long": 50,
    "ema_short": 12,
    "ema_long": 26,
    "bollinger_period": 20,
    "bollinger_std": 2,
}

# Signal Thresholds
SIGNAL_THRESHOLDS = {
    "strong_buy": 80,
    "buy": 60,
    "neutral_high": 55,
    "neutral_low": 45,
    "sell": 40,
    "strong_sell": 20,
}

# API Settings
API_SETTINGS = {
    "coingecko_base_url": "https://api.coingecko.com/api/v3",
    "cache_timeout": 60,  # seconds
    "rate_limit_delay": 1.5,  # seconds between API calls
}

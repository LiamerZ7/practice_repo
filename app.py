"""
Revolut Trading App - Flask Backend
A user-friendly day trading assistant for Revolut-compatible assets
"""

from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
import os

from config import REVOLUT_CRYPTOS, REVOLUT_STOCKS
from data_fetcher import (
    fetch_stock_data, fetch_stock_info, fetch_crypto_prices,
    fetch_crypto_history, get_crypto_by_symbol, get_stock_by_symbol,
    fetch_market_overview, get_trending_assets
)
from technical_analysis import analyze_asset

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# In-memory storage for watchlist and portfolio (in production, use a database)
watchlist = []
portfolio = []


@app.route('/')
def index():
    """Serve the main dashboard"""
    return render_template('index.html')


@app.route('/api/assets/cryptos')
def get_cryptos():
    """Get list of all Revolut-supported cryptocurrencies"""
    return jsonify({"cryptos": REVOLUT_CRYPTOS})


@app.route('/api/assets/stocks')
def get_stocks():
    """Get list of all Revolut-supported stocks"""
    return jsonify({"stocks": REVOLUT_STOCKS})


@app.route('/api/crypto/prices')
def get_crypto_prices():
    """Get current prices for all cryptocurrencies"""
    prices = fetch_crypto_prices()
    return jsonify({"prices": prices})


@app.route('/api/crypto/<symbol>/analyze')
def analyze_crypto(symbol):
    """Get full technical analysis for a cryptocurrency"""
    crypto = get_crypto_by_symbol(symbol)
    if not crypto:
        return jsonify({"error": f"Crypto {symbol} not found"}), 404

    # Fetch historical data
    df = fetch_crypto_history(crypto["coingecko_id"], days=90)
    if df.empty:
        return jsonify({"error": "Could not fetch historical data"}), 500

    # Perform analysis
    analysis = analyze_asset(df)
    if not analysis:
        return jsonify({"error": "Insufficient data for analysis"}), 500

    return jsonify({
        "symbol": symbol,
        "name": crypto["name"],
        "type": "crypto",
        **analysis
    })


@app.route('/api/stock/<symbol>/analyze')
def analyze_stock(symbol):
    """Get full technical analysis for a stock"""
    stock = get_stock_by_symbol(symbol)
    if not stock:
        return jsonify({"error": f"Stock {symbol} not found"}), 404

    # Fetch historical data
    df = fetch_stock_data(symbol, period="3mo", interval="1d")
    if df.empty:
        return jsonify({"error": "Could not fetch historical data"}), 500

    # Get current info
    info = fetch_stock_info(symbol)

    # Perform analysis
    analysis = analyze_asset(df)
    if not analysis:
        return jsonify({"error": "Insufficient data for analysis"}), 500

    return jsonify({
        "symbol": symbol,
        "name": stock["name"],
        "sector": stock.get("sector", "N/A"),
        "type": "stock",
        "info": info,
        **analysis
    })


@app.route('/api/stock/<symbol>/info')
def get_stock_info(symbol):
    """Get current stock information"""
    info = fetch_stock_info(symbol)
    return jsonify(info)


@app.route('/api/market/overview')
def market_overview():
    """Get market overview with major indices"""
    overview = fetch_market_overview()
    return jsonify({"market": overview})


@app.route('/api/trending')
def trending():
    """Get trending assets"""
    asset_type = request.args.get('type', 'all')
    limit = int(request.args.get('limit', 10))
    trending = get_trending_assets(asset_type, limit)
    return jsonify({"trending": trending})


@app.route('/api/signals')
def get_all_signals():
    """Get buy/sell signals for all assets (limited for performance)"""
    signals = []

    # Analyze top cryptos
    prices = fetch_crypto_prices()
    for symbol, data in list(prices.items())[:10]:
        crypto = get_crypto_by_symbol(symbol)
        if crypto:
            df = fetch_crypto_history(crypto["coingecko_id"], days=90)
            if not df.empty:
                analysis = analyze_asset(df)
                if analysis:
                    signals.append({
                        "symbol": symbol,
                        "name": crypto["name"],
                        "type": "crypto",
                        "price": data["price"],
                        "change_24h": data.get("change_24h", 0),
                        "signal": analysis["signal"],
                        "signal_score": analysis["signal_score"],
                        "signal_color": analysis["signal_color"],
                        "rsi": analysis["indicators"]["rsi"],
                    })

    # Analyze top stocks
    for stock in REVOLUT_STOCKS[:10]:
        df = fetch_stock_data(stock["symbol"], period="3mo")
        if not df.empty:
            analysis = analyze_asset(df)
            if analysis:
                signals.append({
                    "symbol": stock["symbol"],
                    "name": stock["name"],
                    "type": "stock",
                    "price": analysis["current_price"],
                    "change_24h": analysis["price_changes"]["1d"],
                    "signal": analysis["signal"],
                    "signal_score": analysis["signal_score"],
                    "signal_color": analysis["signal_color"],
                    "rsi": analysis["indicators"]["rsi"],
                })

    # Sort by signal score (best opportunities first)
    signals.sort(key=lambda x: x["signal_score"], reverse=True)

    return jsonify({"signals": signals})


@app.route('/api/watchlist', methods=['GET', 'POST', 'DELETE'])
def manage_watchlist():
    """Manage user's watchlist"""
    global watchlist

    if request.method == 'GET':
        return jsonify({"watchlist": watchlist})

    elif request.method == 'POST':
        data = request.json
        symbol = data.get('symbol', '').upper()
        asset_type = data.get('type', 'stock')

        # Check if already in watchlist
        if any(w['symbol'] == symbol for w in watchlist):
            return jsonify({"error": "Already in watchlist"}), 400

        watchlist.append({
            "symbol": symbol,
            "type": asset_type,
            "added_at": str(import_datetime())
        })
        return jsonify({"message": f"Added {symbol} to watchlist", "watchlist": watchlist})

    elif request.method == 'DELETE':
        symbol = request.args.get('symbol', '').upper()
        watchlist = [w for w in watchlist if w['symbol'] != symbol]
        return jsonify({"message": f"Removed {symbol} from watchlist", "watchlist": watchlist})


@app.route('/api/portfolio', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_portfolio():
    """Manage user's portfolio"""
    global portfolio

    if request.method == 'GET':
        # Calculate current values
        enriched_portfolio = []
        total_value = 0
        total_cost = 0

        for holding in portfolio:
            current_price = 0
            if holding['type'] == 'crypto':
                prices = fetch_crypto_prices()
                if holding['symbol'] in prices:
                    current_price = prices[holding['symbol']]['price']
            else:
                info = fetch_stock_info(holding['symbol'])
                current_price = info.get('price', 0)

            current_value = current_price * holding['quantity']
            cost_basis = holding['avg_price'] * holding['quantity']
            pnl = current_value - cost_basis
            pnl_percent = ((current_value / cost_basis) - 1) * 100 if cost_basis > 0 else 0

            enriched_portfolio.append({
                **holding,
                "current_price": current_price,
                "current_value": round(current_value, 2),
                "cost_basis": round(cost_basis, 2),
                "pnl": round(pnl, 2),
                "pnl_percent": round(pnl_percent, 2),
            })

            total_value += current_value
            total_cost += cost_basis

        return jsonify({
            "portfolio": enriched_portfolio,
            "total_value": round(total_value, 2),
            "total_cost": round(total_cost, 2),
            "total_pnl": round(total_value - total_cost, 2),
            "total_pnl_percent": round(((total_value / total_cost) - 1) * 100, 2) if total_cost > 0 else 0
        })

    elif request.method == 'POST':
        data = request.json
        symbol = data.get('symbol', '').upper()
        asset_type = data.get('type', 'stock')
        quantity = float(data.get('quantity', 0))
        price = float(data.get('price', 0))

        # Check if already holding
        existing = next((p for p in portfolio if p['symbol'] == symbol), None)
        if existing:
            # Update average price
            total_qty = existing['quantity'] + quantity
            total_cost = (existing['quantity'] * existing['avg_price']) + (quantity * price)
            existing['quantity'] = total_qty
            existing['avg_price'] = total_cost / total_qty
        else:
            portfolio.append({
                "symbol": symbol,
                "type": asset_type,
                "quantity": quantity,
                "avg_price": price,
            })

        return jsonify({"message": f"Added {quantity} {symbol}", "portfolio": portfolio})

    elif request.method == 'DELETE':
        symbol = request.args.get('symbol', '').upper()
        portfolio = [p for p in portfolio if p['symbol'] != symbol]
        return jsonify({"message": f"Removed {symbol} from portfolio", "portfolio": portfolio})


@app.route('/api/screener')
def screener():
    """Screen assets based on criteria"""
    criteria = request.args.get('criteria', 'oversold')  # oversold, overbought, trending, high_volume

    results = []

    # Screen cryptos
    prices = fetch_crypto_prices()
    for symbol, data in prices.items():
        crypto = get_crypto_by_symbol(symbol)
        if crypto:
            df = fetch_crypto_history(crypto["coingecko_id"], days=90)
            if not df.empty:
                analysis = analyze_asset(df)
                if analysis:
                    rsi = analysis["indicators"]["rsi"]
                    include = False

                    if criteria == 'oversold' and rsi < 30:
                        include = True
                    elif criteria == 'overbought' and rsi > 70:
                        include = True
                    elif criteria == 'buy_signals' and analysis["signal"] in ["BUY", "STRONG BUY"]:
                        include = True
                    elif criteria == 'sell_signals' and analysis["signal"] in ["SELL", "STRONG SELL"]:
                        include = True

                    if include:
                        results.append({
                            "symbol": symbol,
                            "name": crypto["name"],
                            "type": "crypto",
                            "price": data["price"],
                            "rsi": rsi,
                            "signal": analysis["signal"],
                            "signal_score": analysis["signal_score"],
                        })

    # Screen stocks (limited for performance)
    for stock in REVOLUT_STOCKS[:20]:
        df = fetch_stock_data(stock["symbol"], period="3mo")
        if not df.empty:
            analysis = analyze_asset(df)
            if analysis:
                rsi = analysis["indicators"]["rsi"]
                include = False

                if criteria == 'oversold' and rsi < 30:
                    include = True
                elif criteria == 'overbought' and rsi > 70:
                    include = True
                elif criteria == 'buy_signals' and analysis["signal"] in ["BUY", "STRONG BUY"]:
                    include = True
                elif criteria == 'sell_signals' and analysis["signal"] in ["SELL", "STRONG SELL"]:
                    include = True

                if include:
                    results.append({
                        "symbol": stock["symbol"],
                        "name": stock["name"],
                        "type": "stock",
                        "price": analysis["current_price"],
                        "rsi": rsi,
                        "signal": analysis["signal"],
                        "signal_score": analysis["signal_score"],
                    })

    results.sort(key=lambda x: x["signal_score"], reverse=(criteria in ['buy_signals', 'oversold']))

    return jsonify({"results": results, "criteria": criteria})


def import_datetime():
    """Import datetime dynamically to avoid circular imports"""
    from datetime import datetime
    return datetime.now()


if __name__ == '__main__':
    # Ensure template and static directories exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)

    print("🚀 Starting Revolut Trading App...")
    print("📊 Dashboard available at http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)

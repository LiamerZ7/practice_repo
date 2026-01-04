"""
Revolut Trading App - Flask Backend
A comprehensive day trading assistant with persistent storage and real-time analysis
"""

import os
from datetime import datetime
from flask import Flask, jsonify, request, render_template, session, g
from flask_cors import CORS

from config import REVOLUT_CRYPTOS, REVOLUT_STOCKS
from models import db, User, Portfolio, Watchlist, Alert, Trade, init_db
from auth_service import auth_service, login_required, get_current_user_optional
from cache_service import cache_manager
from data_fetcher import (
    fetch_stock_data, fetch_stock_info, fetch_crypto_prices,
    fetch_crypto_history, get_crypto_by_symbol, get_stock_by_symbol,
    fetch_market_overview
)
from technical_analysis import analyze_asset

# Create Flask app
app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///trading.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
CORS(app, supports_credentials=True)
init_db(app)


# ===== Frontend Routes =====

@app.route('/')
def index():
    """Serve the main dashboard"""
    return render_template('index.html')


# ===== Auth Routes =====

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.json or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    user, error = auth_service.register_user(username, email, password)

    if error:
        return jsonify({'error': error}), 400

    session['user_id'] = user.id
    return jsonify({'message': 'Registration successful', 'user': user.to_dict()})


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user"""
    data = request.json or {}
    username_or_email = data.get('username', '').strip()
    password = data.get('password', '')

    user, error = auth_service.login_user(username_or_email, password)

    if error:
        return jsonify({'error': error}), 401

    session['user_id'] = user.id
    return jsonify({'message': 'Login successful', 'user': user.to_dict()})


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout user"""
    auth_service.logout_user()
    return jsonify({'message': 'Logged out successfully'})


@app.route('/api/auth/me')
def get_me():
    """Get current user info"""
    user = get_current_user_optional()
    if user:
        return jsonify({'user': user.to_dict()})
    return jsonify({'user': None})


# ===== Asset Routes =====

@app.route('/api/assets/cryptos')
def get_cryptos():
    """Get list of all Revolut-supported cryptocurrencies"""
    return jsonify({"cryptos": REVOLUT_CRYPTOS, "count": len(REVOLUT_CRYPTOS)})


@app.route('/api/assets/stocks')
def get_stocks():
    """Get list of all Revolut-supported stocks"""
    sector = request.args.get('sector')
    if sector:
        filtered = [s for s in REVOLUT_STOCKS if s['sector'].lower() == sector.lower()]
        return jsonify({"stocks": filtered, "count": len(filtered)})
    return jsonify({"stocks": REVOLUT_STOCKS, "count": len(REVOLUT_STOCKS)})


@app.route('/api/assets/sectors')
def get_sectors():
    """Get list of all stock sectors"""
    sectors = list(set(s['sector'] for s in REVOLUT_STOCKS))
    sectors.sort()
    return jsonify({"sectors": sectors})


# ===== Price Routes =====

@app.route('/api/crypto/prices')
def get_crypto_prices():
    """Get current prices for all cryptocurrencies"""
    prices = fetch_crypto_prices()

    # Cache prices in database
    for symbol, data in prices.items():
        cache_manager.set_db_price(symbol, 'crypto', data)

    return jsonify({"prices": prices})


@app.route('/api/stock/<symbol>/price')
def get_stock_price(symbol):
    """Get current price for a stock"""
    # Check cache first
    cached = cache_manager.get_db_price(symbol.upper())
    if cached:
        return jsonify(cached)

    info = fetch_stock_info(symbol.upper())
    if 'error' not in info:
        cache_manager.set_db_price(symbol.upper(), 'stock', {
            'price': info.get('price'),
            'change_24h': info.get('change_percent'),
            'volume_24h': info.get('volume'),
            'market_cap': info.get('market_cap'),
        })
    return jsonify(info)


# ===== Analysis Routes =====

@app.route('/api/crypto/<symbol>/analyze')
def analyze_crypto(symbol):
    """Get full technical analysis for a cryptocurrency"""
    symbol = symbol.upper()

    # Check signal cache
    cached_signal = cache_manager.get_db_signal(symbol)
    if cached_signal:
        crypto = get_crypto_by_symbol(symbol)
        prices = fetch_crypto_prices()
        price_data = prices.get(symbol, {})

        return jsonify({
            "symbol": symbol,
            "name": crypto["name"] if crypto else symbol,
            "type": "crypto",
            "current_price": price_data.get('price', 0),
            "cached": True,
            **cached_signal
        })

    crypto = get_crypto_by_symbol(symbol)
    if not crypto:
        return jsonify({"error": f"Crypto {symbol} not found"}), 404

    df = fetch_crypto_history(crypto["coingecko_id"], days=90)
    if df.empty:
        return jsonify({"error": "Could not fetch historical data"}), 500

    analysis = analyze_asset(df)
    if not analysis:
        return jsonify({"error": "Insufficient data for analysis"}), 500

    # Cache the signal
    cache_manager.set_db_signal(symbol, 'crypto', {
        'signal': analysis['signal'],
        'signal_score': analysis['signal_score'],
        'rsi': analysis['indicators']['rsi'],
        'macd_histogram': analysis['indicators']['macd_histogram'],
        'sma_20': analysis['indicators']['sma_20'],
        'sma_50': analysis['indicators']['sma_50'],
        'analysis_summary': analysis['analysis_summary'],
    })

    return jsonify({
        "symbol": symbol,
        "name": crypto["name"],
        "type": "crypto",
        **analysis
    })


@app.route('/api/stock/<symbol>/analyze')
def analyze_stock(symbol):
    """Get full technical analysis for a stock"""
    symbol = symbol.upper()

    # Check signal cache
    cached_signal = cache_manager.get_db_signal(symbol)
    if cached_signal:
        stock = get_stock_by_symbol(symbol)
        return jsonify({
            "symbol": symbol,
            "name": stock["name"] if stock else symbol,
            "sector": stock.get("sector", "N/A") if stock else "Unknown",
            "type": "stock",
            "cached": True,
            **cached_signal
        })

    stock = get_stock_by_symbol(symbol)
    if not stock:
        stock = {"symbol": symbol, "name": symbol, "sector": "Unknown"}

    df = fetch_stock_data(symbol, period="3mo", interval="1d")
    if df.empty:
        return jsonify({"error": "Could not fetch historical data"}), 500

    analysis = analyze_asset(df)
    if not analysis:
        return jsonify({"error": "Insufficient data for analysis"}), 500

    # Cache the signal
    cache_manager.set_db_signal(symbol, 'stock', {
        'signal': analysis['signal'],
        'signal_score': analysis['signal_score'],
        'rsi': analysis['indicators']['rsi'],
        'macd_histogram': analysis['indicators']['macd_histogram'],
        'sma_20': analysis['indicators']['sma_20'],
        'sma_50': analysis['indicators']['sma_50'],
        'analysis_summary': analysis['analysis_summary'],
    })

    return jsonify({
        "symbol": symbol,
        "name": stock["name"],
        "sector": stock.get("sector", "N/A"),
        "type": "stock",
        **analysis
    })


# ===== Signals Route =====

@app.route('/api/signals')
def get_all_signals():
    """Get buy/sell signals for assets"""
    limit = int(request.args.get('limit', 30))
    asset_type = request.args.get('type')  # 'crypto', 'stock', or None for all

    signals = []

    # Get crypto signals
    if asset_type in [None, 'crypto']:
        prices = fetch_crypto_prices()
        for symbol, data in list(prices.items())[:20]:
            crypto = get_crypto_by_symbol(symbol)
            if crypto:
                # Check cache first
                cached = cache_manager.get_db_signal(symbol)
                if cached:
                    signals.append({
                        "symbol": symbol,
                        "name": crypto["name"],
                        "type": "crypto",
                        "price": data["price"],
                        "change_24h": data.get("change_24h", 0),
                        "signal": cached.get("signal"),
                        "signal_score": cached.get("signal_score"),
                        "signal_color": get_signal_color(cached.get("signal")),
                        "rsi": cached.get("rsi"),
                    })
                else:
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

    # Get stock signals
    if asset_type in [None, 'stock']:
        for stock in REVOLUT_STOCKS[:20]:
            # Check cache first
            cached = cache_manager.get_db_signal(stock["symbol"])
            if cached:
                signals.append({
                    "symbol": stock["symbol"],
                    "name": stock["name"],
                    "type": "stock",
                    "price": cached.get("current_price", 0),
                    "change_24h": 0,
                    "signal": cached.get("signal"),
                    "signal_score": cached.get("signal_score"),
                    "signal_color": get_signal_color(cached.get("signal")),
                    "rsi": cached.get("rsi"),
                })
            else:
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

    # Sort by signal score
    signals.sort(key=lambda x: x.get("signal_score", 0), reverse=True)

    return jsonify({"signals": signals[:limit]})


def get_signal_color(signal):
    """Get color for signal"""
    if not signal:
        return "#FFD700"
    signal = signal.upper()
    if "STRONG BUY" in signal:
        return "#00ff00"
    elif "BUY" in signal:
        return "#90EE90"
    elif "STRONG SELL" in signal:
        return "#FF0000"
    elif "SELL" in signal:
        return "#FFA07A"
    return "#FFD700"


# ===== Portfolio Routes =====

@app.route('/api/portfolio', methods=['GET'])
@login_required
def get_portfolio():
    """Get user's portfolio"""
    holdings = Portfolio.query.filter_by(user_id=g.current_user.id).all()

    enriched = []
    total_value = 0
    total_cost = 0

    prices = fetch_crypto_prices()

    for holding in holdings:
        current_price = 0

        if holding.asset_type == 'crypto':
            if holding.symbol in prices:
                current_price = prices[holding.symbol]['price']
        else:
            info = fetch_stock_info(holding.symbol)
            current_price = info.get('price', 0)

        current_value = current_price * holding.quantity
        cost_basis = holding.avg_price * holding.quantity
        pnl = current_value - cost_basis
        pnl_percent = ((current_value / cost_basis) - 1) * 100 if cost_basis > 0 else 0

        enriched.append({
            **holding.to_dict(),
            "current_price": round(current_price, 4),
            "current_value": round(current_value, 2),
            "cost_basis": round(cost_basis, 2),
            "pnl": round(pnl, 2),
            "pnl_percent": round(pnl_percent, 2),
        })

        total_value += current_value
        total_cost += cost_basis

    return jsonify({
        "portfolio": enriched,
        "total_value": round(total_value, 2),
        "total_cost": round(total_cost, 2),
        "total_pnl": round(total_value - total_cost, 2),
        "total_pnl_percent": round(((total_value / total_cost) - 1) * 100, 2) if total_cost > 0 else 0
    })


@app.route('/api/portfolio', methods=['POST'])
@login_required
def add_to_portfolio():
    """Add or update portfolio holding"""
    data = request.json or {}
    symbol = data.get('symbol', '').upper()
    asset_type = data.get('type', 'stock')
    quantity = float(data.get('quantity', 0))
    price = float(data.get('price', 0))

    if not symbol or quantity <= 0 or price <= 0:
        return jsonify({'error': 'Invalid input'}), 400

    # Check if already holding
    existing = Portfolio.query.filter_by(
        user_id=g.current_user.id,
        symbol=symbol
    ).first()

    if existing:
        # Update average price
        total_qty = existing.quantity + quantity
        total_cost = (existing.quantity * existing.avg_price) + (quantity * price)
        existing.quantity = total_qty
        existing.avg_price = total_cost / total_qty
    else:
        existing = Portfolio(
            user_id=g.current_user.id,
            symbol=symbol,
            asset_type=asset_type,
            quantity=quantity,
            avg_price=price
        )
        db.session.add(existing)

    # Record trade
    trade = Trade(
        user_id=g.current_user.id,
        symbol=symbol,
        asset_type=asset_type,
        trade_type='buy',
        quantity=quantity,
        price=price,
        total_value=quantity * price
    )
    db.session.add(trade)

    try:
        db.session.commit()
        return jsonify({'message': f'Added {quantity} {symbol}', 'holding': existing.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/portfolio/<symbol>', methods=['DELETE'])
@login_required
def remove_from_portfolio(symbol):
    """Remove holding from portfolio"""
    holding = Portfolio.query.filter_by(
        user_id=g.current_user.id,
        symbol=symbol.upper()
    ).first()

    if not holding:
        return jsonify({'error': 'Holding not found'}), 404

    db.session.delete(holding)
    db.session.commit()

    return jsonify({'message': f'Removed {symbol.upper()} from portfolio'})


# ===== Watchlist Routes =====

@app.route('/api/watchlist', methods=['GET'])
@login_required
def get_watchlist():
    """Get user's watchlist"""
    items = Watchlist.query.filter_by(user_id=g.current_user.id).all()
    return jsonify({"watchlist": [item.to_dict() for item in items]})


@app.route('/api/watchlist', methods=['POST'])
@login_required
def add_to_watchlist():
    """Add asset to watchlist"""
    data = request.json or {}
    symbol = data.get('symbol', '').upper()
    asset_type = data.get('type', 'stock')
    notes = data.get('notes', '')
    target_price = data.get('target_price')

    if not symbol:
        return jsonify({'error': 'Symbol required'}), 400

    # Check if already watching
    existing = Watchlist.query.filter_by(
        user_id=g.current_user.id,
        symbol=symbol
    ).first()

    if existing:
        return jsonify({'error': 'Already in watchlist'}), 400

    item = Watchlist(
        user_id=g.current_user.id,
        symbol=symbol,
        asset_type=asset_type,
        notes=notes,
        target_price=target_price
    )
    db.session.add(item)

    try:
        db.session.commit()
        return jsonify({'message': f'Added {symbol} to watchlist', 'item': item.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/watchlist/<symbol>', methods=['DELETE'])
@login_required
def remove_from_watchlist(symbol):
    """Remove asset from watchlist"""
    item = Watchlist.query.filter_by(
        user_id=g.current_user.id,
        symbol=symbol.upper()
    ).first()

    if not item:
        return jsonify({'error': 'Not in watchlist'}), 404

    db.session.delete(item)
    db.session.commit()

    return jsonify({'message': f'Removed {symbol.upper()} from watchlist'})


# ===== Alert Routes =====

@app.route('/api/alerts', methods=['GET'])
@login_required
def get_alerts():
    """Get user's alerts"""
    alerts = Alert.query.filter_by(user_id=g.current_user.id).order_by(Alert.created_at.desc()).all()
    return jsonify({"alerts": [alert.to_dict() for alert in alerts]})


@app.route('/api/alerts', methods=['POST'])
@login_required
def create_alert():
    """Create a new price alert"""
    data = request.json or {}
    symbol = data.get('symbol', '').upper()
    asset_type = data.get('type', 'stock')
    alert_type = data.get('alert_type')  # 'price_above', 'price_below'
    target_value = data.get('target_value')

    if not symbol or not alert_type or target_value is None:
        return jsonify({'error': 'Missing required fields'}), 400

    alert = Alert(
        user_id=g.current_user.id,
        symbol=symbol,
        asset_type=asset_type,
        alert_type=alert_type,
        target_value=float(target_value)
    )
    db.session.add(alert)

    try:
        db.session.commit()
        return jsonify({'message': 'Alert created', 'alert': alert.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/alerts/<int:alert_id>', methods=['DELETE'])
@login_required
def delete_alert(alert_id):
    """Delete an alert"""
    alert = Alert.query.filter_by(
        id=alert_id,
        user_id=g.current_user.id
    ).first()

    if not alert:
        return jsonify({'error': 'Alert not found'}), 404

    db.session.delete(alert)
    db.session.commit()

    return jsonify({'message': 'Alert deleted'})


# ===== Trade History Routes =====

@app.route('/api/trades', methods=['GET'])
@login_required
def get_trades():
    """Get user's trade history"""
    limit = int(request.args.get('limit', 50))
    trades = Trade.query.filter_by(user_id=g.current_user.id)\
        .order_by(Trade.created_at.desc())\
        .limit(limit)\
        .all()
    return jsonify({"trades": [trade.to_dict() for trade in trades]})


# ===== Market Overview Route =====

@app.route('/api/market/overview')
def market_overview():
    """Get market overview with major indices"""
    overview = fetch_market_overview()
    return jsonify({"market": overview})


# ===== Screener Route =====

@app.route('/api/screener')
def screener():
    """Screen assets based on criteria"""
    criteria = request.args.get('criteria', 'oversold')
    limit = int(request.args.get('limit', 20))

    results = []

    # Screen cryptos
    prices = fetch_crypto_prices()
    for symbol, data in list(prices.items())[:30]:
        crypto = get_crypto_by_symbol(symbol)
        if crypto:
            cached = cache_manager.get_db_signal(symbol)
            if cached and cached.get('rsi'):
                rsi = cached['rsi']
                include = False

                if criteria == 'oversold' and rsi < 30:
                    include = True
                elif criteria == 'overbought' and rsi > 70:
                    include = True
                elif criteria == 'buy_signals' and cached.get('signal', '').upper() in ['BUY', 'STRONG BUY']:
                    include = True
                elif criteria == 'sell_signals' and cached.get('signal', '').upper() in ['SELL', 'STRONG SELL']:
                    include = True

                if include:
                    results.append({
                        "symbol": symbol,
                        "name": crypto["name"],
                        "type": "crypto",
                        "price": data["price"],
                        "rsi": rsi,
                        "signal": cached.get("signal"),
                        "signal_score": cached.get("signal_score"),
                    })

    # Sort by relevance
    if criteria in ['buy_signals', 'oversold']:
        results.sort(key=lambda x: x.get("signal_score", 0), reverse=True)
    else:
        results.sort(key=lambda x: x.get("signal_score", 100))

    return jsonify({"results": results[:limit], "criteria": criteria})


# ===== Run Server =====

if __name__ == '__main__':
    # Ensure directories exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)

    # Start background jobs (optional - comment out for serverless)
    # from background_jobs import job_manager
    # job_manager.init_app(app)
    # job_manager.start()

    print("Starting Revolut Trading App...")
    print("Dashboard available at http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)

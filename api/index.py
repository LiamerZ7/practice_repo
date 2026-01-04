"""
Vercel Serverless Function Entry Point
Exports the Flask app for Vercel's Python runtime
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, request, render_template_string, send_from_directory
from flask_cors import CORS

# Import configurations and modules
from config import REVOLUT_CRYPTOS, REVOLUT_STOCKS
from data_fetcher import (
    fetch_stock_data, fetch_stock_info, fetch_crypto_prices,
    fetch_crypto_history, get_crypto_by_symbol, get_stock_by_symbol,
    fetch_market_overview
)
from technical_analysis import analyze_asset

app = Flask(__name__)
CORS(app)

# In-memory storage (note: resets on each serverless invocation)
watchlist = []
portfolio = []


# ===== HTML Template (embedded for serverless) =====
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Revolut Trading Assistant</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #0d1117;
            --bg-secondary: #161b22;
            --bg-tertiary: #21262d;
            --bg-card: #1c2128;
            --text-primary: #f0f6fc;
            --text-secondary: #8b949e;
            --text-muted: #6e7681;
            --border-color: #30363d;
            --accent-blue: #58a6ff;
            --accent-green: #3fb950;
            --accent-red: #f85149;
            --accent-yellow: #d29922;
            --accent-purple: #a371f7;
            --shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
            --radius: 12px;
            --radius-sm: 8px;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header {
            background: var(--bg-secondary);
            padding: 20px;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 24px;
            border-radius: var(--radius);
        }
        .header h1 { font-size: 28px; margin-bottom: 8px; }
        .header h1 span { color: var(--accent-blue); }
        .header p { color: var(--text-secondary); }
        .nav-tabs {
            display: flex;
            gap: 8px;
            margin-bottom: 24px;
            flex-wrap: wrap;
        }
        .nav-tab {
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            color: var(--text-secondary);
            padding: 12px 24px;
            border-radius: var(--radius-sm);
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s;
        }
        .nav-tab:hover, .nav-tab.active {
            background: var(--accent-blue);
            color: white;
            border-color: var(--accent-blue);
        }
        .section { margin-bottom: 32px; }
        .section-title { font-size: 20px; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius);
            padding: 20px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .card:hover {
            transform: translateY(-2px);
            border-color: var(--accent-blue);
            box-shadow: var(--shadow);
        }
        .card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }
        .card-header h3 { font-size: 20px; }
        .card-type {
            font-size: 11px;
            padding: 4px 8px;
            border-radius: 4px;
            background: var(--bg-tertiary);
            color: var(--text-secondary);
            text-transform: uppercase;
        }
        .card-type.crypto { background: rgba(163, 113, 247, 0.2); color: var(--accent-purple); }
        .card-type.stock { background: rgba(88, 166, 255, 0.2); color: var(--accent-blue); }
        .card-name { font-size: 13px; color: var(--text-secondary); margin-bottom: 16px; }
        .card-price { font-size: 24px; font-weight: 600; margin-bottom: 8px; }
        .card-change { font-size: 14px; font-weight: 500; }
        .card-change.positive { color: var(--accent-green); }
        .card-change.negative { color: var(--accent-red); }
        .signal-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            margin-top: 12px;
        }
        .signal-badge.strong-buy { background: rgba(63, 185, 80, 0.2); color: var(--accent-green); }
        .signal-badge.buy { background: rgba(63, 185, 80, 0.15); color: var(--accent-green); }
        .signal-badge.hold { background: rgba(210, 153, 34, 0.2); color: var(--accent-yellow); }
        .signal-badge.sell { background: rgba(248, 81, 73, 0.15); color: var(--accent-red); }
        .signal-badge.strong-sell { background: rgba(248, 81, 73, 0.2); color: var(--accent-red); }
        .score {
            position: absolute;
            top: 16px;
            right: 16px;
            width: 44px;
            height: 44px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 13px;
        }
        .card { position: relative; }
        .loading { text-align: center; padding: 60px; color: var(--text-secondary); }
        .summary-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 32px; }
        .summary-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius);
            padding: 24px;
        }
        .summary-card.buy { border-left: 4px solid var(--accent-green); }
        .summary-card.sell { border-left: 4px solid var(--accent-red); }
        .summary-card h3 { font-size: 18px; margin-bottom: 16px; }
        .suggestion-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid var(--border-color);
            cursor: pointer;
        }
        .suggestion-item:last-child { border-bottom: none; }
        .suggestion-item:hover { background: var(--bg-tertiary); margin: 0 -12px; padding: 12px; border-radius: 8px; }
        .suggestion-info h4 { font-size: 15px; margin-bottom: 4px; }
        .suggestion-info .reason { font-size: 12px; color: var(--text-secondary); }
        .suggestion-score {
            font-size: 13px;
            font-weight: 600;
            padding: 6px 12px;
            border-radius: 16px;
        }
        .suggestion-score.high { background: rgba(63, 185, 80, 0.2); color: var(--accent-green); }
        .suggestion-score.low { background: rgba(248, 81, 73, 0.2); color: var(--accent-red); }
        .search-box {
            display: flex;
            gap: 12px;
            margin-bottom: 24px;
        }
        .search-box input {
            flex: 1;
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-sm);
            padding: 12px 16px;
            color: var(--text-primary);
            font-size: 14px;
        }
        .search-box input::placeholder { color: var(--text-muted); }
        .search-box button {
            background: var(--accent-blue);
            color: white;
            border: none;
            border-radius: var(--radius-sm);
            padding: 12px 24px;
            cursor: pointer;
            font-weight: 500;
        }
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }
        .modal.active { display: flex; }
        .modal-content {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: var(--radius);
            width: 90%;
            max-width: 600px;
            max-height: 90vh;
            overflow-y: auto;
            padding: 32px;
            position: relative;
        }
        .modal-close {
            position: absolute;
            top: 16px;
            right: 20px;
            font-size: 28px;
            color: var(--text-secondary);
            cursor: pointer;
        }
        .modal-header { margin-bottom: 24px; }
        .modal-header h2 { font-size: 28px; margin-bottom: 4px; }
        .modal-header .subtitle { color: var(--text-secondary); }
        .modal-price { font-size: 36px; font-weight: 700; margin-bottom: 24px; }
        .modal-signal {
            background: var(--bg-card);
            border-radius: var(--radius);
            padding: 24px;
            text-align: center;
            margin-bottom: 24px;
        }
        .modal-signal .signal-text { font-size: 24px; font-weight: 700; margin-bottom: 8px; }
        .modal-signal .score { font-size: 48px; font-weight: 700; position: static; width: auto; height: auto; }
        .indicators-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 24px; }
        .indicator {
            background: var(--bg-card);
            border-radius: var(--radius-sm);
            padding: 16px;
        }
        .indicator .label { font-size: 12px; color: var(--text-secondary); margin-bottom: 4px; }
        .indicator .value { font-size: 18px; font-weight: 600; }
        .indicator .status { font-size: 12px; margin-top: 4px; }
        .analysis-list {
            background: var(--bg-card);
            border-radius: var(--radius);
            padding: 20px;
        }
        .analysis-list h3 { font-size: 16px; margin-bottom: 12px; }
        .analysis-list ul { list-style: none; }
        .analysis-list li { padding: 8px 0; border-bottom: 1px solid var(--border-color); font-size: 14px; }
        .analysis-list li:last-child { border-bottom: none; }
        @media (max-width: 768px) {
            .summary-grid { grid-template-columns: 1fr; }
            .grid { grid-template-columns: 1fr; }
            .indicators-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📈 <span>Revolut</span> Trading Assistant</h1>
            <p>Real-time analysis and trading signals for Revolut-compatible assets</p>
        </div>

        <div class="search-box">
            <input type="text" id="search-input" placeholder="Search symbol (e.g., BTC, AAPL, NVDA)">
            <button onclick="searchAsset()">Analyze</button>
        </div>

        <div class="nav-tabs">
            <button class="nav-tab active" onclick="showTab('signals')">🎯 Trading Signals</button>
            <button class="nav-tab" onclick="showTab('crypto')">🪙 Crypto</button>
            <button class="nav-tab" onclick="showTab('stocks')">📊 Stocks</button>
        </div>

        <div id="signals-tab" class="tab-content">
            <div class="summary-grid">
                <div class="summary-card buy">
                    <h3>💚 Consider Buying</h3>
                    <div id="buy-suggestions"><div class="loading">Analyzing...</div></div>
                </div>
                <div class="summary-card sell">
                    <h3>🔴 Consider Selling</h3>
                    <div id="sell-suggestions"><div class="loading">Analyzing...</div></div>
                </div>
            </div>
            <div class="section">
                <h2 class="section-title">🔥 Top Opportunities</h2>
                <div class="grid" id="signals-grid"><div class="loading">Loading signals...</div></div>
            </div>
        </div>

        <div id="crypto-tab" class="tab-content" style="display:none;">
            <div class="section">
                <h2 class="section-title">🪙 Cryptocurrencies</h2>
                <div class="grid" id="crypto-grid"><div class="loading">Loading crypto prices...</div></div>
            </div>
        </div>

        <div id="stocks-tab" class="tab-content" style="display:none;">
            <div class="section">
                <h2 class="section-title">📊 Stocks</h2>
                <div class="grid" id="stocks-grid"><div class="loading">Loading stocks...</div></div>
            </div>
        </div>
    </div>

    <div class="modal" id="modal">
        <div class="modal-content">
            <span class="modal-close" onclick="closeModal()">&times;</span>
            <div id="modal-body"><div class="loading">Loading analysis...</div></div>
        </div>
    </div>

    <script>
        const API = '';

        function formatPrice(p) {
            if (p >= 1) return '$' + p.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
            return '$' + p.toFixed(6);
        }

        function formatChange(c) { return (c >= 0 ? '+' : '') + c.toFixed(2) + '%'; }

        function getSignalClass(s) { return s.toLowerCase().replace(' ', '-'); }

        function showTab(tab) {
            document.querySelectorAll('.tab-content').forEach(t => t.style.display = 'none');
            document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
            document.getElementById(tab + '-tab').style.display = 'block';
            event.target.classList.add('active');

            if (tab === 'crypto') loadCrypto();
            if (tab === 'stocks') loadStocks();
        }

        async function loadSignals() {
            try {
                const res = await fetch(API + '/api/signals');
                const data = await res.json();

                const buys = data.signals.filter(s => s.signal.includes('BUY')).slice(0, 5);
                const sells = data.signals.filter(s => s.signal.includes('SELL')).slice(0, 5);

                document.getElementById('buy-suggestions').innerHTML = buys.length ? buys.map(s => `
                    <div class="suggestion-item" onclick="showDetail('${s.symbol}', '${s.type}')">
                        <div class="suggestion-info">
                            <h4>${s.symbol} - ${s.name}</h4>
                            <span class="reason">RSI: ${s.rsi.toFixed(1)} | ${s.signal}</span>
                        </div>
                        <span class="suggestion-score high">${s.signal_score}</span>
                    </div>
                `).join('') : '<p style="color:var(--text-muted)">No strong buy signals</p>';

                document.getElementById('sell-suggestions').innerHTML = sells.length ? sells.map(s => `
                    <div class="suggestion-item" onclick="showDetail('${s.symbol}', '${s.type}')">
                        <div class="suggestion-info">
                            <h4>${s.symbol} - ${s.name}</h4>
                            <span class="reason">RSI: ${s.rsi.toFixed(1)} | ${s.signal}</span>
                        </div>
                        <span class="suggestion-score low">${s.signal_score}</span>
                    </div>
                `).join('') : '<p style="color:var(--text-muted)">No strong sell signals</p>';

                document.getElementById('signals-grid').innerHTML = data.signals.slice(0, 12).map(s => `
                    <div class="card" onclick="showDetail('${s.symbol}', '${s.type}')">
                        <div class="score" style="background:${s.signal_color}20;color:${s.signal_color}">${s.signal_score}</div>
                        <div class="card-header">
                            <h3>${s.symbol}</h3>
                            <span class="card-type ${s.type}">${s.type}</span>
                        </div>
                        <div class="card-name">${s.name}</div>
                        <div class="card-price">${formatPrice(s.price)}</div>
                        <div class="card-change ${s.change_24h >= 0 ? 'positive' : 'negative'}">${formatChange(s.change_24h)}</div>
                        <div class="signal-badge ${getSignalClass(s.signal)}">${s.signal}</div>
                    </div>
                `).join('');
            } catch (e) {
                document.getElementById('signals-grid').innerHTML = '<div class="loading">Error loading signals</div>';
            }
        }

        async function loadCrypto() {
            try {
                const res = await fetch(API + '/api/crypto/prices');
                const data = await res.json();

                document.getElementById('crypto-grid').innerHTML = Object.entries(data.prices).map(([sym, c]) => `
                    <div class="card" onclick="showDetail('${sym}', 'crypto')">
                        <div class="card-header">
                            <h3>${sym}</h3>
                            <span class="card-type crypto">CRYPTO</span>
                        </div>
                        <div class="card-name">${c.name}</div>
                        <div class="card-price">${formatPrice(c.price)}</div>
                        <div class="card-change ${c.change_24h >= 0 ? 'positive' : 'negative'}">${formatChange(c.change_24h)}</div>
                    </div>
                `).join('');
            } catch (e) {
                document.getElementById('crypto-grid').innerHTML = '<div class="loading">Error loading crypto</div>';
            }
        }

        async function loadStocks() {
            try {
                const res = await fetch(API + '/api/assets/stocks');
                const data = await res.json();

                document.getElementById('stocks-grid').innerHTML = data.stocks.slice(0, 50).map(s => `
                    <div class="card" onclick="showDetail('${s.symbol}', 'stock')">
                        <div class="card-header">
                            <h3>${s.symbol}</h3>
                            <span class="card-type stock">${s.sector}</span>
                        </div>
                        <div class="card-name">${s.name}</div>
                    </div>
                `).join('');
            } catch (e) {
                document.getElementById('stocks-grid').innerHTML = '<div class="loading">Error loading stocks</div>';
            }
        }

        async function showDetail(symbol, type) {
            document.getElementById('modal').classList.add('active');
            document.getElementById('modal-body').innerHTML = '<div class="loading">Analyzing ' + symbol + '...</div>';

            const endpoint = type === 'crypto' ? `/api/crypto/${symbol}/analyze` : `/api/stock/${symbol}/analyze`;

            try {
                const res = await fetch(API + endpoint);
                const d = await res.json();

                if (d.error) {
                    document.getElementById('modal-body').innerHTML = '<div class="loading">Error: ' + d.error + '</div>';
                    return;
                }

                document.getElementById('modal-body').innerHTML = `
                    <div class="modal-header">
                        <h2>${d.symbol}</h2>
                        <p class="subtitle">${d.name}</p>
                    </div>
                    <div class="modal-price">${formatPrice(d.current_price)}
                        <span class="${d.price_changes['1d'] >= 0 ? 'positive' : 'negative'}" style="font-size:18px;margin-left:12px">
                            ${formatChange(d.price_changes['1d'])}
                        </span>
                    </div>
                    <div class="modal-signal">
                        <div class="signal-text" style="color:${d.signal_color}">${d.signal_icon} ${d.signal}</div>
                        <div class="score" style="color:${d.signal_color}">${d.signal_score}/100</div>
                    </div>
                    <div class="indicators-grid">
                        <div class="indicator">
                            <div class="label">RSI (14)</div>
                            <div class="value">${d.indicators.rsi}</div>
                            <div class="status" style="color:${d.indicators.rsi > 70 ? 'var(--accent-red)' : d.indicators.rsi < 30 ? 'var(--accent-green)' : 'var(--text-secondary)'}">
                                ${d.indicators.rsi_status}
                            </div>
                        </div>
                        <div class="indicator">
                            <div class="label">MACD</div>
                            <div class="value">${d.indicators.macd_histogram > 0 ? '+' : ''}${d.indicators.macd_histogram.toFixed(4)}</div>
                            <div class="status" style="color:${d.indicators.macd_status === 'Bullish' ? 'var(--accent-green)' : 'var(--accent-red)'}">
                                ${d.indicators.macd_status}
                            </div>
                        </div>
                        <div class="indicator">
                            <div class="label">SMA 20 / 50</div>
                            <div class="value">${formatPrice(d.indicators.sma_20)}</div>
                            <div class="status">${formatPrice(d.indicators.sma_50)}</div>
                        </div>
                        <div class="indicator">
                            <div class="label">BB Position</div>
                            <div class="value">${d.indicators.bb_position}%</div>
                            <div class="status">${d.indicators.bb_position < 20 ? 'Near Lower' : d.indicators.bb_position > 80 ? 'Near Upper' : 'Middle'}</div>
                        </div>
                    </div>
                    <div class="analysis-list">
                        <h3>Analysis Summary</h3>
                        <ul>${d.analysis_summary.map(p => '<li>' + p + '</li>').join('')}</ul>
                    </div>
                `;
            } catch (e) {
                document.getElementById('modal-body').innerHTML = '<div class="loading">Error loading analysis</div>';
            }
        }

        function closeModal() { document.getElementById('modal').classList.remove('active'); }

        function searchAsset() {
            const q = document.getElementById('search-input').value.toUpperCase().trim();
            if (q) showDetail(q, 'stock');
        }

        document.getElementById('search-input').addEventListener('keypress', e => { if (e.key === 'Enter') searchAsset(); });

        // Auto-load signals on page load
        loadSignals();
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    """Serve the main dashboard"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/assets/cryptos')
def get_cryptos():
    """Get list of all Revolut-supported cryptocurrencies"""
    return jsonify({"cryptos": REVOLUT_CRYPTOS})


@app.route('/api/assets/stocks')
def get_stocks():
    """Get list of all Revolut-supported stocks"""
    return jsonify({"stocks": REVOLUT_STOCKS})


@app.route('/api/crypto/prices')
def get_crypto_prices_route():
    """Get current prices for all cryptocurrencies"""
    prices = fetch_crypto_prices()
    return jsonify({"prices": prices})


@app.route('/api/crypto/<symbol>/analyze')
def analyze_crypto(symbol):
    """Get full technical analysis for a cryptocurrency"""
    crypto = get_crypto_by_symbol(symbol)
    if not crypto:
        return jsonify({"error": f"Crypto {symbol} not found"}), 404

    df = fetch_crypto_history(crypto["coingecko_id"], days=90)
    if df.empty:
        return jsonify({"error": "Could not fetch historical data"}), 500

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
        # Try anyway - might be a valid symbol not in our list
        stock = {"symbol": symbol, "name": symbol, "sector": "Unknown"}

    df = fetch_stock_data(symbol, period="3mo", interval="1d")
    if df.empty:
        return jsonify({"error": "Could not fetch historical data"}), 500

    analysis = analyze_asset(df)
    if not analysis:
        return jsonify({"error": "Insufficient data for analysis"}), 500

    return jsonify({
        "symbol": symbol,
        "name": stock["name"],
        "sector": stock.get("sector", "N/A"),
        "type": "stock",
        **analysis
    })


@app.route('/api/signals')
def get_all_signals():
    """Get buy/sell signals for assets"""
    signals = []

    # Analyze top cryptos (limited for performance on serverless)
    prices = fetch_crypto_prices()
    for symbol, data in list(prices.items())[:15]:
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
    for stock in REVOLUT_STOCKS[:15]:
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

    signals.sort(key=lambda x: x["signal_score"], reverse=True)
    return jsonify({"signals": signals})


@app.route('/api/market/overview')
def market_overview():
    """Get market overview"""
    overview = fetch_market_overview()
    return jsonify({"market": overview})


# Vercel handler
def handler(request):
    """Vercel serverless function handler"""
    return app(request)


if __name__ == '__main__':
    app.run(debug=True, port=5000)

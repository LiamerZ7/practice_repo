/**
 * Revolut Trading Assistant - Frontend JavaScript
 * Provides interactive trading signals and portfolio management
 */

// API Base URL
const API_BASE = '';

// Cache for API responses
const cache = {};
const CACHE_DURATION = 30000; // 30 seconds

// ===== Utility Functions =====

function formatPrice(price, decimals = 2) {
    if (price >= 1) {
        return price.toLocaleString('de-DE', { minimumFractionDigits: decimals, maximumFractionDigits: decimals }) + ' €';
    }
    return price.toFixed(6) + ' €';
}

function formatChange(change) {
    const sign = change >= 0 ? '+' : '';
    return sign + change.toFixed(2) + '%';
}

function formatLargeNumber(num) {
    if (num >= 1e12) return (num / 1e12).toFixed(2) + 'T';
    if (num >= 1e9) return (num / 1e9).toFixed(2) + 'B';
    if (num >= 1e6) return (num / 1e6).toFixed(2) + 'M';
    if (num >= 1e3) return (num / 1e3).toFixed(2) + 'K';
    return num.toFixed(2);
}

function getSignalClass(signal) {
    return signal.toLowerCase().replace(' ', '-');
}

function getChangeClass(change) {
    return change >= 0 ? 'positive' : 'negative';
}

async function fetchWithCache(url, cacheKey, duration = CACHE_DURATION) {
    const now = Date.now();
    if (cache[cacheKey] && (now - cache[cacheKey].timestamp) < duration) {
        return cache[cacheKey].data;
    }

    try {
        const response = await fetch(API_BASE + url);
        const data = await response.json();
        cache[cacheKey] = { data, timestamp: now };
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// ===== Page Navigation =====

const navItems = document.querySelectorAll('.nav-item');
const pages = document.querySelectorAll('.page');
const pageTitle = document.getElementById('page-title');
const pageSubtitle = document.getElementById('page-subtitle');

const pageTitles = {
    dashboard: { title: 'Dashboard', subtitle: 'Overview of your trading opportunities' },
    signals: { title: 'Trading Signals', subtitle: 'Comprehensive buy/sell recommendations' },
    screener: { title: 'Asset Screener', subtitle: 'Find assets matching specific criteria' },
    cryptos: { title: 'Cryptocurrencies', subtitle: 'Revolut-supported crypto assets' },
    stocks: { title: 'Stocks', subtitle: 'Popular stocks available on Revolut' },
    portfolio: { title: 'My Portfolio', subtitle: 'Track your holdings and performance' },
    watchlist: { title: 'Watchlist', subtitle: 'Assets you\'re monitoring' }
};

navItems.forEach(item => {
    item.addEventListener('click', () => {
        const page = item.dataset.page;

        // Update active nav
        navItems.forEach(n => n.classList.remove('active'));
        item.classList.add('active');

        // Show page
        pages.forEach(p => p.classList.remove('active'));
        document.getElementById(`${page}-page`).classList.add('active');

        // Update header
        pageTitle.textContent = pageTitles[page].title;
        pageSubtitle.textContent = pageTitles[page].subtitle;

        // Load page data
        loadPageData(page);
    });
});

function loadPageData(page) {
    switch (page) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'signals':
            loadSignals();
            break;
        case 'cryptos':
            loadCryptos();
            break;
        case 'stocks':
            loadStocks();
            break;
        case 'portfolio':
            loadPortfolio();
            break;
        case 'watchlist':
            loadWatchlist();
            break;
    }
}

// ===== Dashboard =====

async function loadDashboard() {
    loadMarketOverview();
    loadQuickSignals();
    loadBuySellSuggestions();
}

async function loadMarketOverview() {
    const container = document.getElementById('market-overview');
    container.innerHTML = '<div class="loading">Loading market data...</div>';

    try {
        const data = await fetchWithCache('/api/market/overview', 'market-overview');

        let html = '';
        for (const [symbol, info] of Object.entries(data.market)) {
            const changeClass = getChangeClass(info.change);
            html += `
                <div class="market-card">
                    <h3>${info.name}</h3>
                    <div class="price">${formatPrice(info.price)}</div>
                    <div class="change ${changeClass}">${formatChange(info.change)}</div>
                </div>
            `;
        }

        container.innerHTML = html || '<div class="loading">Market data unavailable</div>';
    } catch (error) {
        container.innerHTML = '<div class="loading">Error loading market data</div>';
    }
}

async function loadQuickSignals() {
    const container = document.getElementById('quick-signals');
    container.innerHTML = '<div class="loading">Analyzing assets...</div>';

    try {
        const data = await fetchWithCache('/api/signals', 'signals', 60000);

        // Get top opportunities (highest scores)
        const topSignals = data.signals.slice(0, 6);

        let html = '';
        topSignals.forEach(signal => {
            const changeKey = signal.type === 'crypto' ? 'change_24h' : 'change_24h';
            const change = signal[changeKey] || 0;
            const changeClass = getChangeClass(change);
            const signalClass = getSignalClass(signal.signal);

            html += `
                <div class="signal-card" onclick="showAssetDetail('${signal.symbol}', '${signal.type}')">
                    <div class="signal-score" style="background: ${signal.signal_color}20; color: ${signal.signal_color}">
                        ${signal.signal_score}
                    </div>
                    <div class="signal-card-header">
                        <h3>${signal.symbol}</h3>
                        <span class="type ${signal.type}">${signal.type}</span>
                    </div>
                    <div class="name">${signal.name}</div>
                    <div class="price-row">
                        <span class="price">${formatPrice(signal.price)}</span>
                        <span class="change ${changeClass}">${formatChange(change)}</span>
                    </div>
                    <div class="signal-badge ${signalClass}">
                        ${signal.signal}
                    </div>
                </div>
            `;
        });

        container.innerHTML = html || '<div class="loading">No signals available</div>';
    } catch (error) {
        container.innerHTML = '<div class="loading">Error loading signals</div>';
    }
}

async function loadBuySellSuggestions() {
    const buyContainer = document.getElementById('buy-suggestions');
    const sellContainer = document.getElementById('sell-suggestions');

    buyContainer.innerHTML = '<div class="loading">Analyzing...</div>';
    sellContainer.innerHTML = '<div class="loading">Analyzing...</div>';

    try {
        const data = await fetchWithCache('/api/signals', 'signals', 60000);

        // Filter buy and sell signals
        const buySignals = data.signals
            .filter(s => s.signal.includes('BUY'))
            .slice(0, 5);
        const sellSignals = data.signals
            .filter(s => s.signal.includes('SELL'))
            .slice(0, 5);

        // Render buy suggestions
        let buyHtml = '';
        buySignals.forEach(signal => {
            buyHtml += `
                <div class="suggestion-item" onclick="showAssetDetail('${signal.symbol}', '${signal.type}')">
                    <div class="suggestion-info">
                        <h4>${signal.symbol} - ${signal.name}</h4>
                        <span class="reason">RSI: ${signal.rsi.toFixed(1)} | ${signal.signal}</span>
                    </div>
                    <span class="suggestion-score high">${signal.signal_score}</span>
                </div>
            `;
        });
        buyContainer.innerHTML = buyHtml || '<p class="placeholder-text">No strong buy signals</p>';

        // Render sell suggestions
        let sellHtml = '';
        sellSignals.forEach(signal => {
            sellHtml += `
                <div class="suggestion-item" onclick="showAssetDetail('${signal.symbol}', '${signal.type}')">
                    <div class="suggestion-info">
                        <h4>${signal.symbol} - ${signal.name}</h4>
                        <span class="reason">RSI: ${signal.rsi.toFixed(1)} | ${signal.signal}</span>
                    </div>
                    <span class="suggestion-score low">${signal.signal_score}</span>
                </div>
            `;
        });
        sellContainer.innerHTML = sellHtml || '<p class="placeholder-text">No strong sell signals</p>';

    } catch (error) {
        buyContainer.innerHTML = '<div class="loading">Error loading</div>';
        sellContainer.innerHTML = '<div class="loading">Error loading</div>';
    }
}

// ===== Signals Page =====

let allSignals = [];
let currentFilter = 'all';

async function loadSignals() {
    const tbody = document.getElementById('signals-tbody');
    tbody.innerHTML = '<tr><td colspan="8" class="loading">Loading signals...</td></tr>';

    try {
        const data = await fetchWithCache('/api/signals', 'signals', 60000);
        allSignals = data.signals;
        renderSignalsTable(allSignals);
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="8" class="loading">Error loading signals</td></tr>';
    }
}

function renderSignalsTable(signals) {
    const tbody = document.getElementById('signals-tbody');

    let html = '';
    signals.forEach(signal => {
        const change = signal.change_24h || 0;
        const changeClass = getChangeClass(change);
        const signalClass = getSignalClass(signal.signal);

        html += `
            <tr>
                <td><span class="symbol">${signal.symbol}</span><br><small>${signal.name}</small></td>
                <td><span class="type ${signal.type}">${signal.type}</span></td>
                <td>${formatPrice(signal.price)}</td>
                <td class="${changeClass}">${formatChange(change)}</td>
                <td>${signal.rsi.toFixed(1)}</td>
                <td><span class="signal-badge ${signalClass}">${signal.signal}</span></td>
                <td><strong>${signal.signal_score}</strong>/100</td>
                <td><button class="action-btn" onclick="showAssetDetail('${signal.symbol}', '${signal.type}')">Analyze</button></td>
            </tr>
        `;
    });

    tbody.innerHTML = html || '<tr><td colspan="8" class="loading">No signals found</td></tr>';
}

// Filter buttons
document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        const filter = btn.dataset.filter;
        currentFilter = filter;

        let filtered = allSignals;

        if (filter === 'buy') {
            filtered = allSignals.filter(s => s.signal.includes('BUY'));
        } else if (filter === 'sell') {
            filtered = allSignals.filter(s => s.signal.includes('SELL'));
        } else if (filter === 'crypto') {
            filtered = allSignals.filter(s => s.type === 'crypto');
        } else if (filter === 'stock') {
            filtered = allSignals.filter(s => s.type === 'stock');
        }

        renderSignalsTable(filtered);
    });
});

// ===== Screener =====

document.querySelectorAll('.screener-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
        const criteria = btn.dataset.criteria;
        const container = document.getElementById('screener-results');
        container.innerHTML = '<div class="loading">Screening assets...</div>';

        try {
            const response = await fetch(`${API_BASE}/api/screener?criteria=${criteria}`);
            const data = await response.json();

            if (data.results.length === 0) {
                container.innerHTML = '<p class="placeholder-text">No assets match this criteria</p>';
                return;
            }

            let html = '<div class="signals-grid">';
            data.results.forEach(result => {
                const signalClass = getSignalClass(result.signal);
                html += `
                    <div class="signal-card" onclick="showAssetDetail('${result.symbol}', '${result.type}')">
                        <div class="signal-card-header">
                            <h3>${result.symbol}</h3>
                            <span class="type ${result.type}">${result.type}</span>
                        </div>
                        <div class="name">${result.name}</div>
                        <div class="price-row">
                            <span class="price">${formatPrice(result.price)}</span>
                            <span>RSI: ${result.rsi.toFixed(1)}</span>
                        </div>
                        <div class="signal-badge ${signalClass}">${result.signal}</div>
                    </div>
                `;
            });
            html += '</div>';

            container.innerHTML = html;
        } catch (error) {
            container.innerHTML = '<div class="loading">Error screening assets</div>';
        }
    });
});

// ===== Cryptos Page =====

async function loadCryptos() {
    const container = document.getElementById('crypto-grid');
    container.innerHTML = '<div class="loading">Loading cryptocurrencies...</div>';

    try {
        const data = await fetchWithCache('/api/crypto/prices', 'crypto-prices');

        let html = '';
        for (const [symbol, crypto] of Object.entries(data.prices)) {
            const changeClass = getChangeClass(crypto.change_24h);
            html += `
                <div class="asset-card" onclick="showAssetDetail('${symbol}', 'crypto')">
                    <div class="asset-card-header">
                        <h3>${symbol}</h3>
                    </div>
                    <div class="name">${crypto.name}</div>
                    <div class="price">${formatPrice(crypto.price)}</div>
                    <div class="change ${changeClass}">${formatChange(crypto.change_24h)}</div>
                </div>
            `;
        }

        container.innerHTML = html || '<div class="loading">No cryptocurrencies found</div>';
    } catch (error) {
        container.innerHTML = '<div class="loading">Error loading cryptocurrencies</div>';
    }
}

// ===== Stocks Page =====

let allStocks = [];

async function loadStocks() {
    const container = document.getElementById('stock-grid');
    const filterContainer = document.getElementById('sector-filter');
    container.innerHTML = '<div class="loading">Loading stocks...</div>';

    try {
        const data = await fetchWithCache('/api/assets/stocks', 'stocks-list', 300000);
        allStocks = data.stocks;

        // Get unique sectors
        const sectors = [...new Set(allStocks.map(s => s.sector))];
        let filterHtml = '<button class="sector-btn active" data-sector="all">All</button>';
        sectors.forEach(sector => {
            filterHtml += `<button class="sector-btn" data-sector="${sector}">${sector}</button>`;
        });
        filterContainer.innerHTML = filterHtml;

        // Add click handlers to sector buttons
        document.querySelectorAll('.sector-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.sector-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                filterStocks(btn.dataset.sector);
            });
        });

        renderStocks(allStocks);
    } catch (error) {
        container.innerHTML = '<div class="loading">Error loading stocks</div>';
    }
}

function filterStocks(sector) {
    if (sector === 'all') {
        renderStocks(allStocks);
    } else {
        renderStocks(allStocks.filter(s => s.sector === sector));
    }
}

function renderStocks(stocks) {
    const container = document.getElementById('stock-grid');

    let html = '';
    stocks.forEach(stock => {
        html += `
            <div class="asset-card" onclick="showAssetDetail('${stock.symbol}', 'stock')">
                <div class="asset-card-header">
                    <h3>${stock.symbol}</h3>
                    <span class="type stock">${stock.sector}</span>
                </div>
                <div class="name">${stock.name}</div>
            </div>
        `;
    });

    container.innerHTML = html || '<div class="loading">No stocks found</div>';
}

// ===== Portfolio =====

async function loadPortfolio() {
    const holdings = document.getElementById('portfolio-holdings');
    holdings.innerHTML = '<div class="loading">Loading portfolio...</div>';

    try {
        const response = await fetch(`${API_BASE}/api/portfolio`);
        const data = await response.json();

        // Update summary
        document.getElementById('total-value').textContent = formatPrice(data.total_value);
        document.getElementById('total-pnl').textContent = formatPrice(data.total_pnl);
        document.getElementById('total-pnl').className = 'stat-value ' + getChangeClass(data.total_pnl);
        document.getElementById('total-pnl-percent').textContent = formatChange(data.total_pnl_percent);
        document.getElementById('total-pnl-percent').className = 'stat-value ' + getChangeClass(data.total_pnl_percent);

        if (data.portfolio.length === 0) {
            holdings.innerHTML = '<p class="placeholder-text">No holdings yet. Add your first position above!</p>';
            return;
        }

        let html = '';
        data.portfolio.forEach(holding => {
            const pnlClass = getChangeClass(holding.pnl);
            html += `
                <div class="holding-item">
                    <div class="holding-info">
                        <h4>${holding.symbol}</h4>
                        <span class="details">${holding.quantity} shares @ ${formatPrice(holding.avg_price)}</span>
                    </div>
                    <div class="holding-value">
                        <div class="current">${formatPrice(holding.current_value)}</div>
                        <div class="pnl ${pnlClass}">${formatPrice(holding.pnl)} (${formatChange(holding.pnl_percent)})</div>
                    </div>
                </div>
            `;
        });

        holdings.innerHTML = html;
    } catch (error) {
        holdings.innerHTML = '<div class="loading">Error loading portfolio</div>';
    }
}

// Add holding form
document.getElementById('add-holding-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const symbol = document.getElementById('holding-symbol').value.toUpperCase();
    const type = document.getElementById('holding-type').value;
    const quantity = parseFloat(document.getElementById('holding-quantity').value);
    const price = parseFloat(document.getElementById('holding-price').value);

    try {
        const response = await fetch(`${API_BASE}/api/portfolio`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol, type, quantity, price })
        });

        if (response.ok) {
            document.getElementById('add-holding-form').reset();
            loadPortfolio();
        }
    } catch (error) {
        alert('Error adding holding');
    }
});

// ===== Watchlist =====

async function loadWatchlist() {
    const container = document.getElementById('watchlist-items');
    container.innerHTML = '<div class="loading">Loading watchlist...</div>';

    try {
        const response = await fetch(`${API_BASE}/api/watchlist`);
        const data = await response.json();

        if (data.watchlist.length === 0) {
            container.innerHTML = '<p class="placeholder-text">Your watchlist is empty. Add assets to track!</p>';
            return;
        }

        let html = '<div class="signals-grid">';
        for (const item of data.watchlist) {
            html += `
                <div class="signal-card" onclick="showAssetDetail('${item.symbol}', '${item.type}')">
                    <div class="signal-card-header">
                        <h3>${item.symbol}</h3>
                        <span class="type ${item.type}">${item.type}</span>
                    </div>
                    <button class="action-btn" onclick="event.stopPropagation(); removeFromWatchlist('${item.symbol}')">Remove</button>
                </div>
            `;
        }
        html += '</div>';

        container.innerHTML = html;
    } catch (error) {
        container.innerHTML = '<div class="loading">Error loading watchlist</div>';
    }
}

// Add to watchlist form
document.getElementById('add-watchlist-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const symbol = document.getElementById('watchlist-symbol').value.toUpperCase();
    const type = document.getElementById('watchlist-type').value;

    try {
        const response = await fetch(`${API_BASE}/api/watchlist`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol, type })
        });

        if (response.ok) {
            document.getElementById('add-watchlist-form').reset();
            loadWatchlist();
        }
    } catch (error) {
        alert('Error adding to watchlist');
    }
});

async function removeFromWatchlist(symbol) {
    try {
        await fetch(`${API_BASE}/api/watchlist?symbol=${symbol}`, { method: 'DELETE' });
        loadWatchlist();
    } catch (error) {
        alert('Error removing from watchlist');
    }
}

// ===== Asset Detail Modal =====

const modal = document.getElementById('asset-modal');
const modalBody = document.getElementById('modal-body');

document.querySelector('.modal-close').addEventListener('click', () => {
    modal.classList.remove('active');
});

modal.addEventListener('click', (e) => {
    if (e.target === modal) {
        modal.classList.remove('active');
    }
});

async function showAssetDetail(symbol, type) {
    modal.classList.add('active');
    modalBody.innerHTML = '<div class="loading">Loading analysis...</div>';

    const endpoint = type === 'crypto' ? `/api/crypto/${symbol}/analyze` : `/api/stock/${symbol}/analyze`;

    try {
        const response = await fetch(API_BASE + endpoint);
        const data = await response.json();

        if (data.error) {
            modalBody.innerHTML = `<div class="loading">Error: ${data.error}</div>`;
            return;
        }

        const changeClass = getChangeClass(data.price_changes['1d']);
        const signalClass = getSignalClass(data.signal);

        modalBody.innerHTML = `
            <div class="modal-header">
                <div>
                    <h2>${data.symbol}</h2>
                    <p class="subtitle">${data.name}</p>
                </div>
                <div class="modal-price">
                    <div class="price">${formatPrice(data.current_price)}</div>
                    <div class="change ${changeClass}">24h: ${formatChange(data.price_changes['1d'])}</div>
                </div>
            </div>

            <div class="modal-signal">
                <div class="signal-text" style="color: ${data.signal_color}">${data.signal_icon} ${data.signal}</div>
                <div class="score" style="color: ${data.signal_color}">${data.signal_score}/100</div>
            </div>

            <div class="modal-indicators">
                <div class="indicator-card">
                    <div class="label">RSI (14)</div>
                    <div class="value">${data.indicators.rsi}</div>
                    <div class="status ${data.indicators.rsi_status === 'Overbought' ? 'negative' : data.indicators.rsi_status === 'Oversold' ? 'positive' : ''}">${data.indicators.rsi_status}</div>
                </div>
                <div class="indicator-card">
                    <div class="label">MACD</div>
                    <div class="value">${data.indicators.macd_histogram > 0 ? '+' : ''}${data.indicators.macd_histogram.toFixed(4)}</div>
                    <div class="status ${data.indicators.macd_status === 'Bullish' ? 'positive' : 'negative'}">${data.indicators.macd_status}</div>
                </div>
                <div class="indicator-card">
                    <div class="label">SMA 20</div>
                    <div class="value">${formatPrice(data.indicators.sma_20)}</div>
                </div>
                <div class="indicator-card">
                    <div class="label">SMA 50</div>
                    <div class="value">${formatPrice(data.indicators.sma_50)}</div>
                </div>
                <div class="indicator-card">
                    <div class="label">BB Position</div>
                    <div class="value">${data.indicators.bb_position}%</div>
                    <div class="status">${data.indicators.bb_position < 20 ? 'Near Lower' : data.indicators.bb_position > 80 ? 'Near Upper' : 'Middle'}</div>
                </div>
                <div class="indicator-card">
                    <div class="label">Price Changes</div>
                    <div class="value">
                        <span class="${getChangeClass(data.price_changes['7d'])}">${formatChange(data.price_changes['7d'])} (7d)</span>
                    </div>
                    <div class="status">
                        <span class="${getChangeClass(data.price_changes['30d'])}">${formatChange(data.price_changes['30d'])} (30d)</span>
                    </div>
                </div>
            </div>

            <div class="modal-analysis">
                <h3>Analysis Summary</h3>
                <ul>
                    ${data.analysis_summary.map(point => `<li>${point}</li>`).join('')}
                </ul>
            </div>
        `;
    } catch (error) {
        modalBody.innerHTML = '<div class="loading">Error loading analysis</div>';
    }
}

// ===== Search =====

document.getElementById('search-btn').addEventListener('click', performSearch);
document.getElementById('search-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') performSearch();
});

async function performSearch() {
    const query = document.getElementById('search-input').value.toUpperCase().trim();
    if (!query) return;

    // Try crypto first, then stock
    try {
        const cryptoResponse = await fetch(`${API_BASE}/api/crypto/${query}/analyze`);
        if (cryptoResponse.ok) {
            const data = await cryptoResponse.json();
            if (!data.error) {
                showAssetDetail(query, 'crypto');
                return;
            }
        }
    } catch (e) {}

    try {
        const stockResponse = await fetch(`${API_BASE}/api/stock/${query}/analyze`);
        if (stockResponse.ok) {
            const data = await stockResponse.json();
            if (!data.error) {
                showAssetDetail(query, 'stock');
                return;
            }
        }
    } catch (e) {}

    alert(`Asset "${query}" not found. Make sure it's available on Revolut.`);
}

// ===== Refresh =====

document.getElementById('refresh-btn').addEventListener('click', () => {
    // Clear cache
    Object.keys(cache).forEach(key => delete cache[key]);

    // Reload current page
    const activePage = document.querySelector('.nav-item.active').dataset.page;
    loadPageData(activePage);
});

// ===== Initialize =====

document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
});

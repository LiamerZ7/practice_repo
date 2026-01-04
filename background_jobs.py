"""
Background Jobs for Revolut Trading App
Handles periodic data refresh, alert checking, and signal updates
"""

import json
from datetime import datetime
from threading import Thread
import time


class BackgroundJobManager:
    """Manages background tasks"""

    def __init__(self, app=None):
        self.app = app
        self.running = False
        self._threads = []

    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app

    def start(self):
        """Start all background jobs"""
        if self.running:
            return

        self.running = True

        # Price refresh job (every 2 minutes)
        t1 = Thread(target=self._price_refresh_loop, daemon=True)
        t1.start()
        self._threads.append(t1)

        # Signal refresh job (every 10 minutes)
        t2 = Thread(target=self._signal_refresh_loop, daemon=True)
        t2.start()
        self._threads.append(t2)

        # Alert check job (every 1 minute)
        t3 = Thread(target=self._alert_check_loop, daemon=True)
        t3.start()
        self._threads.append(t3)

        print("Background jobs started")

    def stop(self):
        """Stop all background jobs"""
        self.running = False
        print("Background jobs stopped")

    def _price_refresh_loop(self):
        """Periodically refresh price cache"""
        while self.running:
            try:
                with self.app.app_context():
                    self._refresh_prices()
            except Exception as e:
                print(f"Price refresh error: {e}")
            time.sleep(120)  # 2 minutes

    def _signal_refresh_loop(self):
        """Periodically refresh signal cache"""
        while self.running:
            try:
                with self.app.app_context():
                    self._refresh_signals()
            except Exception as e:
                print(f"Signal refresh error: {e}")
            time.sleep(600)  # 10 minutes

    def _alert_check_loop(self):
        """Periodically check price alerts"""
        while self.running:
            try:
                with self.app.app_context():
                    self._check_alerts()
            except Exception as e:
                print(f"Alert check error: {e}")
            time.sleep(60)  # 1 minute

    def _refresh_prices(self):
        """Refresh cached prices for top assets"""
        from data_fetcher import fetch_crypto_prices
        from cache_service import cache_manager
        from config import REVOLUT_CRYPTOS

        print(f"[{datetime.now()}] Refreshing price cache...")

        # Refresh crypto prices
        try:
            prices = fetch_crypto_prices()
            for symbol, data in prices.items():
                cache_manager.set_db_price(symbol, 'crypto', data)
        except Exception as e:
            print(f"Error refreshing crypto prices: {e}")

    def _refresh_signals(self):
        """Refresh cached signals for top assets"""
        from data_fetcher import (
            fetch_crypto_prices, fetch_crypto_history,
            fetch_stock_data, get_crypto_by_symbol
        )
        from technical_analysis import analyze_asset
        from cache_service import cache_manager
        from config import REVOLUT_STOCKS

        print(f"[{datetime.now()}] Refreshing signal cache...")

        # Refresh crypto signals (top 20)
        try:
            prices = fetch_crypto_prices()
            for symbol in list(prices.keys())[:20]:
                crypto = get_crypto_by_symbol(symbol)
                if crypto:
                    df = fetch_crypto_history(crypto["coingecko_id"], days=90)
                    if not df.empty:
                        analysis = analyze_asset(df)
                        if analysis:
                            signal_data = {
                                'signal': analysis['signal'],
                                'signal_score': analysis['signal_score'],
                                'rsi': analysis['indicators']['rsi'],
                                'macd_histogram': analysis['indicators']['macd_histogram'],
                                'sma_20': analysis['indicators']['sma_20'],
                                'sma_50': analysis['indicators']['sma_50'],
                                'analysis_summary': analysis['analysis_summary'],
                            }
                            cache_manager.set_db_signal(symbol, 'crypto', signal_data)
        except Exception as e:
            print(f"Error refreshing crypto signals: {e}")

        # Refresh stock signals (top 20)
        try:
            for stock in REVOLUT_STOCKS[:20]:
                df = fetch_stock_data(stock["symbol"], period="3mo")
                if not df.empty:
                    analysis = analyze_asset(df)
                    if analysis:
                        signal_data = {
                            'signal': analysis['signal'],
                            'signal_score': analysis['signal_score'],
                            'rsi': analysis['indicators']['rsi'],
                            'macd_histogram': analysis['indicators']['macd_histogram'],
                            'sma_20': analysis['indicators']['sma_20'],
                            'sma_50': analysis['indicators']['sma_50'],
                            'analysis_summary': analysis['analysis_summary'],
                        }
                        cache_manager.set_db_signal(stock["symbol"], 'stock', signal_data)
        except Exception as e:
            print(f"Error refreshing stock signals: {e}")

    def _check_alerts(self):
        """Check and trigger price alerts"""
        from models import Alert, db
        from data_fetcher import fetch_crypto_prices, fetch_stock_info
        from cache_service import cache_manager

        print(f"[{datetime.now()}] Checking alerts...")

        # Get all active alerts
        alerts = Alert.query.filter_by(is_active=True, is_triggered=False).all()

        if not alerts:
            return

        # Get current prices
        crypto_prices = {}
        try:
            crypto_prices = fetch_crypto_prices()
        except:
            pass

        for alert in alerts:
            try:
                current_price = None

                if alert.asset_type == 'crypto':
                    if alert.symbol in crypto_prices:
                        current_price = crypto_prices[alert.symbol]['price']
                else:
                    # For stocks, check cache first
                    cached = cache_manager.get_db_price(alert.symbol)
                    if cached:
                        current_price = cached.get('price')
                    else:
                        info = fetch_stock_info(alert.symbol)
                        current_price = info.get('price')

                if current_price is None:
                    continue

                # Check alert conditions
                triggered = False

                if alert.alert_type == 'price_above' and current_price >= alert.target_value:
                    triggered = True
                elif alert.alert_type == 'price_below' and current_price <= alert.target_value:
                    triggered = True

                if triggered:
                    alert.is_triggered = True
                    alert.triggered_at = datetime.utcnow()
                    print(f"Alert triggered: {alert.symbol} {alert.alert_type} {alert.target_value}")

            except Exception as e:
                print(f"Error checking alert {alert.id}: {e}")

        try:
            db.session.commit()
        except:
            db.session.rollback()


# Global job manager instance
job_manager = BackgroundJobManager()

"""
Caching Service for Revolut Trading App
Provides in-memory and database caching for API responses
"""

import json
import time
from datetime import datetime, timedelta
from functools import wraps
from threading import Lock

# In-memory cache with TTL
_memory_cache = {}
_cache_lock = Lock()


class CacheManager:
    """Manages both in-memory and database caching"""

    def __init__(self, db=None):
        self.db = db
        self.default_ttl = 60  # seconds

    def get_memory(self, key):
        """Get value from memory cache"""
        with _cache_lock:
            if key in _memory_cache:
                item = _memory_cache[key]
                if time.time() < item['expires']:
                    return item['value']
                else:
                    del _memory_cache[key]
        return None

    def set_memory(self, key, value, ttl=None):
        """Set value in memory cache"""
        if ttl is None:
            ttl = self.default_ttl
        with _cache_lock:
            _memory_cache[key] = {
                'value': value,
                'expires': time.time() + ttl
            }

    def delete_memory(self, key):
        """Delete value from memory cache"""
        with _cache_lock:
            if key in _memory_cache:
                del _memory_cache[key]

    def clear_memory(self):
        """Clear all memory cache"""
        with _cache_lock:
            _memory_cache.clear()

    def get_db_price(self, symbol):
        """Get cached price from database"""
        from models import CachedPrice
        cache = CachedPrice.query.filter_by(symbol=symbol).first()
        if cache:
            # Check if cache is fresh (within 5 minutes)
            if cache.last_updated and datetime.utcnow() - cache.last_updated < timedelta(minutes=5):
                return cache.to_dict()
        return None

    def set_db_price(self, symbol, asset_type, price_data):
        """Set cached price in database"""
        from models import CachedPrice, db

        cache = CachedPrice.query.filter_by(symbol=symbol).first()
        if cache:
            cache.price = price_data.get('price')
            cache.change_24h = price_data.get('change_24h')
            cache.volume_24h = price_data.get('volume_24h')
            cache.market_cap = price_data.get('market_cap')
            cache.last_updated = datetime.utcnow()
        else:
            cache = CachedPrice(
                symbol=symbol,
                asset_type=asset_type,
                price=price_data.get('price'),
                change_24h=price_data.get('change_24h'),
                volume_24h=price_data.get('volume_24h'),
                market_cap=price_data.get('market_cap'),
                last_updated=datetime.utcnow()
            )
            db.session.add(cache)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error caching price for {symbol}: {e}")

    def get_db_signal(self, symbol):
        """Get cached signal from database"""
        from models import CachedSignal
        cache = CachedSignal.query.filter_by(symbol=symbol).first()
        if cache:
            # Check if cache is fresh (within 15 minutes)
            if cache.last_updated and datetime.utcnow() - cache.last_updated < timedelta(minutes=15):
                return cache.to_dict()
        return None

    def set_db_signal(self, symbol, asset_type, signal_data):
        """Set cached signal in database"""
        from models import CachedSignal, db

        cache = CachedSignal.query.filter_by(symbol=symbol).first()
        analysis_json = json.dumps(signal_data.get('analysis_summary', []))

        if cache:
            cache.signal = signal_data.get('signal')
            cache.signal_score = signal_data.get('signal_score')
            cache.rsi = signal_data.get('rsi')
            cache.macd_histogram = signal_data.get('macd_histogram')
            cache.sma_20 = signal_data.get('sma_20')
            cache.sma_50 = signal_data.get('sma_50')
            cache.analysis_summary = analysis_json
            cache.last_updated = datetime.utcnow()
        else:
            cache = CachedSignal(
                symbol=symbol,
                asset_type=asset_type,
                signal=signal_data.get('signal'),
                signal_score=signal_data.get('signal_score'),
                rsi=signal_data.get('rsi'),
                macd_histogram=signal_data.get('macd_histogram'),
                sma_20=signal_data.get('sma_20'),
                sma_50=signal_data.get('sma_50'),
                analysis_summary=analysis_json,
                last_updated=datetime.utcnow()
            )
            db.session.add(cache)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error caching signal for {symbol}: {e}")

    def get_all_cached_signals(self, max_age_minutes=15):
        """Get all cached signals that are still fresh"""
        from models import CachedSignal
        cutoff = datetime.utcnow() - timedelta(minutes=max_age_minutes)
        signals = CachedSignal.query.filter(CachedSignal.last_updated >= cutoff).all()
        return [s.to_dict() for s in signals]


# Decorator for caching function results
def cached(ttl=60, key_prefix=''):
    """Decorator to cache function results in memory"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"

            # Check cache
            cached_value = cache_manager.get_memory(cache_key)
            if cached_value is not None:
                return cached_value

            # Call function and cache result
            result = func(*args, **kwargs)
            cache_manager.set_memory(cache_key, result, ttl)
            return result
        return wrapper
    return decorator


# Global cache manager instance
cache_manager = CacheManager()

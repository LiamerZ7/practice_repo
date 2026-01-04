"""
Database Models for Revolut Trading App
Uses SQLAlchemy with SQLite (easily upgradable to PostgreSQL)
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    """User account model"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Relationships
    portfolios = db.relationship('Portfolio', backref='user', lazy=True, cascade='all, delete-orphan')
    watchlist = db.relationship('Watchlist', backref='user', lazy=True, cascade='all, delete-orphan')
    alerts = db.relationship('Alert', backref='user', lazy=True, cascade='all, delete-orphan')
    trades = db.relationship('Trade', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
        }


class Portfolio(db.Model):
    """User portfolio holdings"""
    __tablename__ = 'portfolios'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    asset_type = db.Column(db.String(20), nullable=False)  # 'crypto' or 'stock'
    quantity = db.Column(db.Float, nullable=False)
    avg_price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'symbol', name='unique_user_symbol'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'asset_type': self.asset_type,
            'quantity': self.quantity,
            'avg_price': self.avg_price,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class Watchlist(db.Model):
    """User watchlist"""
    __tablename__ = 'watchlists'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    asset_type = db.Column(db.String(20), nullable=False)
    notes = db.Column(db.Text)
    target_price = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'symbol', name='unique_user_watchlist_symbol'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'asset_type': self.asset_type,
            'notes': self.notes,
            'target_price': self.target_price,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Alert(db.Model):
    """Price alerts"""
    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    asset_type = db.Column(db.String(20), nullable=False)
    alert_type = db.Column(db.String(20), nullable=False)  # 'price_above', 'price_below', 'rsi_above', 'rsi_below'
    target_value = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    is_triggered = db.Column(db.Boolean, default=False)
    triggered_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'asset_type': self.asset_type,
            'alert_type': self.alert_type,
            'target_value': self.target_value,
            'is_active': self.is_active,
            'is_triggered': self.is_triggered,
            'triggered_at': self.triggered_at.isoformat() if self.triggered_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Trade(db.Model):
    """Trade history"""
    __tablename__ = 'trades'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    asset_type = db.Column(db.String(20), nullable=False)
    trade_type = db.Column(db.String(10), nullable=False)  # 'buy' or 'sell'
    quantity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    total_value = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'asset_type': self.asset_type,
            'trade_type': self.trade_type,
            'quantity': self.quantity,
            'price': self.price,
            'total_value': self.total_value,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class CachedPrice(db.Model):
    """Cached price data for faster access"""
    __tablename__ = 'cached_prices'

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), nullable=False, unique=True)
    asset_type = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Float)
    change_24h = db.Column(db.Float)
    volume_24h = db.Column(db.Float)
    market_cap = db.Column(db.Float)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'symbol': self.symbol,
            'asset_type': self.asset_type,
            'price': self.price,
            'change_24h': self.change_24h,
            'volume_24h': self.volume_24h,
            'market_cap': self.market_cap,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
        }


class CachedSignal(db.Model):
    """Cached trading signals"""
    __tablename__ = 'cached_signals'

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), nullable=False, unique=True)
    asset_type = db.Column(db.String(20), nullable=False)
    signal = db.Column(db.String(20))
    signal_score = db.Column(db.Float)
    rsi = db.Column(db.Float)
    macd_histogram = db.Column(db.Float)
    sma_20 = db.Column(db.Float)
    sma_50 = db.Column(db.Float)
    analysis_summary = db.Column(db.Text)  # JSON string
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        import json
        return {
            'symbol': self.symbol,
            'asset_type': self.asset_type,
            'signal': self.signal,
            'signal_score': self.signal_score,
            'rsi': self.rsi,
            'macd_histogram': self.macd_histogram,
            'sma_20': self.sma_20,
            'sma_50': self.sma_50,
            'analysis_summary': json.loads(self.analysis_summary) if self.analysis_summary else [],
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
        }


def init_db(app):
    """Initialize the database"""
    db.init_app(app)
    with app.app_context():
        db.create_all()

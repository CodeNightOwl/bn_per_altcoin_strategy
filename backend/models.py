from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Coin(db.Model):
    __tablename__ = 'coins'
    
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    change_24h = db.Column(db.Float, nullable=False)
    change_1h = db.Column(db.Float, nullable=True)
    volume_24h = db.Column(db.Float, nullable=True)
    market_cap = db.Column(db.Float, nullable=True)
    is_altcoin = db.Column(db.Boolean, default=True, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'name': self.name,
            'price': self.price,
            'change_24h': self.change_24h,
            'change_1h': self.change_1h,
            'volume_24h': self.volume_24h,
            'market_cap': self.market_cap,
            'is_altcoin': self.is_altcoin,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class CoinHistory(db.Model):
    __tablename__ = 'coin_history'
    
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), nullable=False, index=True)
    price = db.Column(db.Float, nullable=False)
    change_24h = db.Column(db.Float, nullable=False)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'price': self.price,
            'change_24h': self.change_24h,
            'recorded_at': self.recorded_at.isoformat()
        }
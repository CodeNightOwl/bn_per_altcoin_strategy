import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-123456')
    
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 3007))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    DB_TYPE = os.getenv('DB_TYPE', 'sqlite')
    
    if DB_TYPE == 'mysql':
        MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
        MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
        MYSQL_USER = os.getenv('MYSQL_USER', 'root')
        MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
        MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'crypto_monitor')
        MYSQL_CHARSET = os.getenv('MYSQL_CHARSET', 'utf8mb4')
        
        SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset={MYSQL_CHARSET}'
    else:
        SQLITE_DB_PATH = os.getenv('SQLITE_DB_PATH', 'crypto_monitor.db')
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{SQLITE_DB_PATH}'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    BINANCE_API_KEY = os.getenv('BINANCE_API_KEY', '')
    BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET', '')
    BINANCE_ENABLE_RATE_LIMIT = os.getenv('BINANCE_ENABLE_RATE_LIMIT', 'True').lower() == 'true'
    
    MIN_VOLUME_USD = float(os.getenv('MIN_VOLUME_USD', 5000000))
    MAX_COINS_LIMIT = int(os.getenv('MAX_COINS_LIMIT', 500))
    EXCLUDE_STABLECOINS = os.getenv('EXCLUDE_STABLECOINS', 'True').lower() == 'true'
    
    SHORT_TERM_CHANGE_THRESHOLD = float(os.getenv('SHORT_TERM_CHANGE_THRESHOLD', 5.0))
    SHORT_TERM_TIMEFRAME = os.getenv('SHORT_TERM_TIMEFRAME', '1h')
    ENABLE_SHORT_TERM_DETECTION = os.getenv('ENABLE_SHORT_TERM_DETECTION', 'True').lower() == 'true'

    # 信号推送 (ingest API) 配置
    SIGNAL_PUSH_ENABLED = os.getenv('SIGNAL_PUSH_ENABLED', 'True').lower() == 'true'
    INGEST_BASE_URL = os.getenv('INGEST_BASE_URL', 'https://www.hxdxm.com')
    INGEST_TOKEN = os.getenv('INGEST_TOKEN', '')
    INGEST_SOURCE = os.getenv('INGEST_SOURCE', 'crypto_monitor')
    SIGNAL_5M_THRESHOLD = float(os.getenv('SIGNAL_5M_THRESHOLD', 2.0))
    SIGNAL_1M_THRESHOLD = float(os.getenv('SIGNAL_1M_THRESHOLD', 0.8))
    SIGNAL_VOLUME_THRESHOLD = float(os.getenv('SIGNAL_VOLUME_THRESHOLD', 5000000))
    SIGNAL_5M_COOLDOWN_SECONDS = int(os.getenv('SIGNAL_5M_COOLDOWN_SECONDS', 600))
    SIGNAL_1M_COOLDOWN_SECONDS = int(os.getenv('SIGNAL_1M_COOLDOWN_SECONDS', 300))
    SIGNAL_SCAN_INTERVAL = int(os.getenv('SIGNAL_SCAN_INTERVAL', 30))
    
    MAJOR_COINS = set(os.getenv('MAJOR_COINS', 'BTC,ETH,BNB,USDT,USDC,BUSD,DAI,XRP,ADA,DOGE,SOL,DOT,MATIC,SHIB,LTC,TRX,AVAX,LINK,ATOM,UNI').split(','))
    
    COIN_UPDATE_INTERVAL = int(os.getenv('COIN_UPDATE_INTERVAL', 60))
    AUTO_UPDATE_ENABLED = os.getenv('AUTO_UPDATE_ENABLED', 'False').lower() == 'true'
    
    CORS_ENABLED = os.getenv('CORS_ENABLED', 'True').lower() == 'true'
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')
    
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
    
    DEFAULT_PAGE_SIZE = int(os.getenv('DEFAULT_PAGE_SIZE', 50))
    MAX_PAGE_SIZE = int(os.getenv('MAX_PAGE_SIZE', 200))
from flask import Flask
from flask_cors import CORS
from config import Config
from models import db
from routes import api_bp
import logging
import os
import threading
import time

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    if Config.CORS_ENABLED:
        CORS(app, origins=Config.CORS_ORIGINS)

    db.init_app(app)

    app.register_blueprint(api_bp)

    log_dir = os.path.dirname(Config.LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(Config.LOG_FILE),
            logging.StreamHandler()
        ]
    )

    with app.app_context():
        db.create_all()

    return app

app = create_app()

# ---- Auto-start market data service on import ----
def _start_market_data():
    from market_data import get_market_data
    md = get_market_data()
    if not md.is_running:
        md.start()
        print("Market data service started (Binance REST)")

threading.Thread(target=_start_market_data, daemon=True).start()

if __name__ == '__main__':
    if Config.FLASK_DEBUG:
        # 本地开发：使用 Flask 自带开发服务器（带重载）
        app.run(
            host=Config.FLASK_HOST,
            port=Config.FLASK_PORT,
            debug=True
        )
    else:
        # 生产：使用 waitress（多线程 WSGI 服务器），关闭 debug/reloader
        from waitress import serve
        serve(app, host=Config.FLASK_HOST, port=Config.FLASK_PORT, threads=8)

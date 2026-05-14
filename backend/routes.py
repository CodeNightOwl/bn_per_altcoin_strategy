from flask import Blueprint, jsonify, request
from flask_cors import CORS
from models import db, Coin, CoinHistory
from binance_service import BinanceService
from market_data import get_market_data
from config import Config
import logging

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)

if Config.CORS_ENABLED:
    CORS(api_bp, origins=Config.CORS_ORIGINS)

binance_service = BinanceService(
    api_key=Config.BINANCE_API_KEY,
    api_secret=Config.BINANCE_API_SECRET,
    enable_rate_limit=Config.BINANCE_ENABLE_RATE_LIMIT
)

def _md():
    return get_market_data()


@api_bp.route('/api/coins/update', methods=['POST'])
def update_coins():
    """Sync coins from REST to DB (one-time). For initial seeding only."""
    try:
        tickers = binance_service.fetch_all_tickers()
        if not tickers:
            return jsonify({'error': 'Failed to fetch tickers'}), 500

        altcoins = binance_service.filter_altcoins(tickers)

        updated_count = 0
        for coin_data in altcoins:
            coin = Coin.query.filter_by(symbol=coin_data['symbol']).first()
            if coin:
                coin.price = coin_data['price']
                coin.change_24h = coin_data['change_24h']
                coin.change_1h = coin_data['change_1h']
                coin.volume_24h = coin_data['volume_24h']
                coin.market_cap = coin_data['market_cap']
                coin.is_altcoin = coin_data['is_altcoin']
            else:
                coin = Coin(**coin_data)
                db.session.add(coin)
            updated_count += 1

        db.session.commit()
        return jsonify({'success': True, 'message': f'Updated {updated_count} coins', 'count': updated_count})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating coins: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/api/coins', methods=['GET'])
def get_coins():
    """Get coins from DB (seeded data)."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', Config.DEFAULT_PAGE_SIZE, type=int), Config.MAX_PAGE_SIZE)
        sort_by = request.args.get('sort_by', 'change_24h')
        order = request.args.get('order', 'desc')

        query = Coin.query.filter_by(is_altcoin=True)

        sort_map = {
            'change_24h': Coin.change_24h,
            'change_1h': Coin.change_1h,
            'volume_24h': Coin.volume_24h,
            'price': Coin.price
        }
        sort_column = sort_map.get(sort_by, Coin.change_24h)

        query = query.order_by(sort_column.desc() if order == 'desc' else sort_column.asc())

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'coins': [coin.to_dict() for coin in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        })
    except Exception as e:
        logger.error(f"Error getting coins: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/api/coins/timeframe-changes', methods=['GET'])
def get_timeframe_changes():
    """Get coins with multi-timeframe changes from market data cache."""
    try:
        volume_threshold = request.args.get('volume_threshold', Config.MIN_VOLUME_USD, type=float)
        limit = request.args.get('limit', 100, type=int)
        timeframes = request.args.get('timeframes', '1m,5m,15m,30m,1h', type=str).split(',')

        md = _md()
        all_tickers = md.get_all_tickers()

        coins_with_changes = []
        for base, ticker in all_tickers.items():
            vol = ticker.get('volume_24h', 0)
            if vol < volume_threshold:
                continue
            if base in Config.MAJOR_COINS:
                continue

            sym = f"{base}/USDT"
            changes = md.get_timeframe_changes(sym, timeframes)

            coin_dict = {
                'symbol': sym,
                'name': base,
                'price': ticker['price'],
                'change_24h': ticker['change_24h'],
                'volume_24h': vol,
                'change_1h': ticker.get('change_1h', 0),
                'market_cap': 0,
                'updated_at': ticker.get('updated_at', 0)
            }
            coin_dict.update(changes)

            vals = [changes.get(f'change_{tf}', 0) or 0 for tf in timeframes]
            coin_dict['max_change'] = max(vals, key=abs) if vals else 0

            coins_with_changes.append(coin_dict)

        coins_with_changes.sort(key=lambda x: abs(x['max_change']), reverse=True)
        coins_with_changes = coins_with_changes[:limit]

        # Fetch klines for top coins that don't have data yet
        need_klines = [
            c['symbol'] for c in coins_with_changes[:50]
            if not md.has_kline_data(c['symbol'])
        ]
        if need_klines:
            md.ensure_kline_streams(need_klines, timeframes)

        return jsonify({
            'coins': coins_with_changes,
            'timeframes': timeframes,
            'volume_threshold': volume_threshold,
            'is_live': md.is_running,
            'ticker_count': md.get_ticker_count()
        })
    except Exception as e:
        logger.error(f"Error getting timeframe changes: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/api/coins/short-term-movers', methods=['GET'])
def get_short_term_movers():
    """Get short-term movers from market data cache."""
    try:
        threshold = request.args.get('threshold', Config.SHORT_TERM_CHANGE_THRESHOLD, type=float)
        volume_threshold = request.args.get('volume_threshold', Config.MIN_VOLUME_USD, type=float)
        limit = request.args.get('limit', 50, type=int)
        timeframe = request.args.get('timeframe', '5m', type=str)

        md = _md()
        all_tickers = md.get_all_tickers()

        top = md.get_top_volume_symbols(80)
        if top:
            md.ensure_kline_streams(top, [timeframe])

        gainers, losers = [], []
        for base, ticker in all_tickers.items():
            vol = ticker.get('volume_24h', 0)
            if vol < volume_threshold or base in Config.MAJOR_COINS:
                continue

            sym = f"{base}/USDT"
            change = md.get_timeframe_change(sym, timeframe)

            if change is None or abs(change) < threshold:
                continue

            coin_dict = {
                'symbol': sym,
                'name': base,
                'price': ticker['price'],
                'change_24h': ticker['change_24h'],
                'change_1h': ticker.get('change_1h', 0),
                'volume_24h': vol,
                'short_term_change': change
            }

            if change >= 0:
                gainers.append(coin_dict)
            else:
                losers.append(coin_dict)

        gainers.sort(key=lambda x: abs(x['short_term_change']), reverse=True)
        losers.sort(key=lambda x: abs(x['short_term_change']), reverse=True)

        return jsonify({
            'gainers': gainers[:limit],
            'losers': losers[:limit],
            'threshold': threshold,
            'volume_threshold': volume_threshold,
            'timeframe': timeframe,
            'is_live': md.is_running
        })
    except Exception as e:
        logger.error(f"Error getting short term movers: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/api/coins/extreme', methods=['GET'])
def get_extreme_movers():
    """Get 1-minute extreme movers from market data cache."""
    try:
        threshold = request.args.get('threshold', 3.0, type=float)
        volume_threshold = request.args.get('volume_threshold', Config.MIN_VOLUME_USD, type=float)
        limit = request.args.get('limit', 50, type=int)

        md = _md()
        all_tickers = md.get_all_tickers()

        top = md.get_top_volume_symbols(80)
        if top:
            md.ensure_kline_streams(top, ['1m'])

        coins = []
        for base, ticker in all_tickers.items():
            vol = ticker.get('volume_24h', 0)
            if vol < volume_threshold or base in Config.MAJOR_COINS:
                continue

            sym = f"{base}/USDT"
            change_1m = md.get_timeframe_change(sym, '1m')

            coin_dict = {
                'symbol': sym,
                'name': base,
                'price': ticker['price'],
                'change_1m': change_1m,
                'change_24h': ticker['change_24h'],
                'volume_24h': vol,
                'market_cap': 0,
                'max_change': change_1m or 0
            }
            coins.append(coin_dict)

        coins.sort(key=lambda x: abs(x['max_change']), reverse=True)

        gainers = [c for c in coins if (c['change_1m'] or 0) >= threshold][:limit]
        losers = [c for c in coins if (c['change_1m'] or 0) <= -threshold][:limit]

        return jsonify({
            'gainers': gainers,
            'losers': losers,
            'threshold': threshold,
            'is_live': md.is_running
        })
    except Exception as e:
        logger.error(f"Error getting extreme movers: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/api/stats', methods=['GET'])
def get_stats():
    """Get stats from market data cache."""
    try:
        md = _md()
        all_tickers = md.get_all_tickers()

        alt_tickers = {
            k: v for k, v in all_tickers.items()
            if k not in Config.MAJOR_COINS
        }

        total = len(alt_tickers)
        changes = [t['change_24h'] for t in alt_tickers.values()]
        avg_change = sum(changes) / len(changes) if changes else 0
        gainers = sum(1 for c in changes if c > 0)
        losers = sum(1 for c in changes if c < 0)

        return jsonify({
            'total_altcoins': total,
            'avg_change_24h': round(avg_change, 2),
            'gainers_count': gainers,
            'losers_count': losers
        })
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/api/coins/<symbol>', methods=['GET'])
def get_coin_detail(symbol):
    try:
        md = _md()
        ticker = md.get_ticker(symbol)
        changes = md.get_timeframe_changes(symbol, ['1m', '5m', '15m', '30m', '1h'])

        if not ticker:
            return jsonify({'error': 'Coin not found'}), 404

        return jsonify({
            'coin': {**ticker, **changes},
        })
    except Exception as e:
        logger.error(f"Error getting coin detail: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/api/coins/klines', methods=['GET'])
def get_coin_klines():
    try:
        symbol = request.args.get('symbol', '', type=str)
        timeframe = request.args.get('timeframe', '5m', type=str)
        limit = min(request.args.get('limit', 100, type=int), 200)
        if not symbol:
            return jsonify({'error': 'symbol required'}), 400
        md = _md()
        klines = md.fetch_recent_klines(symbol, timeframe, limit)
        return jsonify({'symbol': symbol, 'timeframe': timeframe, 'klines': klines})
    except Exception as e:
        logger.error(f"Error getting klines: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/api/config', methods=['GET'])
def get_config():
    return jsonify({
        'min_volume_usd': Config.MIN_VOLUME_USD,
        'short_term_change_threshold': Config.SHORT_TERM_CHANGE_THRESHOLD,
        'short_term_timeframe': Config.SHORT_TERM_TIMEFRAME,
        'enable_short_term_detection': Config.ENABLE_SHORT_TERM_DETECTION
    })


@api_bp.route('/api/health', methods=['GET'])
def health_check():
    md = _md()
    return jsonify({
        'status': 'ok',
        'ws_connected': md.is_running,
        'ticker_count': md.get_ticker_count()
    })


@api_bp.route('/api/ws/status', methods=['GET'])
def market_data_status():
    md = _md()
    return jsonify({
        'connected': md.is_running,
        'ticker_count': md.get_ticker_count()
    })


@api_bp.route('/api/ws/data', methods=['GET'])
def get_market_data_raw():
    md = _md()
    if not md.is_running:
        return jsonify({'error': 'Data service not running'}), 400
    all_tickers = md.get_all_tickers()
    return jsonify({
        'success': True,
        'data': all_tickers,
        'count': len(all_tickers)
    })

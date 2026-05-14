import json
import logging
import threading
import time
from typing import Dict, List, Optional
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import websocket
import ccxt
from config import Config

logger = logging.getLogger(__name__)

class BinanceWebSocketService:
    def __init__(self, api_key: str = '', api_secret: str = ''):
        self.api_key = api_key
        self.api_secret = api_secret
        self.ws = None
        self.ws_thread = None
        self.is_running = False
        self._lock = threading.Lock()

        # All-market ticker data: base -> {price, change_24h, volume_24h, ...}
        self.tickers: Dict[str, dict] = {}

        # Kline cache: base -> {timeframe -> [kline_prev, kline_curr]}
        self.klines: Dict[str, Dict[str, list]] = defaultdict(lambda: defaultdict(list))

        # Track subscribed streams
        self._kline_subs: set = set()
        self._pending_subs: list = []

        self._executor = ThreadPoolExecutor(max_workers=10)

        self.reconnect_interval = 3
        self.max_reconnect_attempts = 50
        self.reconnect_attempts = 0

        self.exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })

    # ---- WebSocket handlers ----

    def on_open(self, ws):
        logger.info("WebSocket connected")
        self.is_running = True
        self.reconnect_attempts = 0
        pending = list(self._pending_subs)
        self._pending_subs.clear()
        if pending:
            self._send_subscribe(pending)

    def on_message(self, ws, raw):
        try:
            data = json.loads(raw)
            stream = data.get('stream', '')
            if stream == '!miniTicker@arr':
                self._handle_mini_tickers(data.get('data', []))
            elif '@kline_' in stream:
                parts = stream.split('@')
                sym = parts[0].upper()
                tf = parts[1].replace('kline_', '')
                k = data.get('data', {}).get('k', {})
                if k:
                    self._handle_kline(sym, tf, k)
        except Exception:
            pass

    def on_error(self, ws, error):
        logger.error(f"WS error: {error}")

    def on_close(self, ws, code, msg):
        logger.info(f"WS closed (code={code})")
        self.is_running = False
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            delay = min(self.reconnect_interval * (1.5 ** (self.reconnect_attempts - 1)), 30)
            time.sleep(delay)
            self.connect()

    def _handle_mini_tickers(self, tickers: list):
        with self._lock:
            for t in tickers:
                sym = t.get('s', '')
                if not sym.endswith('USDT'):
                    continue
                base = sym.replace('USDT', '')
                self.tickers[base] = {
                    'symbol': f"{base}/USDT",
                    'name': base,
                    'price': float(t.get('c', 0)),
                    'change_24h': float(t.get('P', 0)),
                    'volume_24h': float(t.get('q', 0)),
                    'high_24h': float(t.get('h', 0)),
                    'low_24h': float(t.get('l', 0)),
                    'updated_at': time.time()
                }

    def _handle_kline(self, symbol: str, timeframe: str, k: dict):
        entry = {
            'open': float(k.get('o', 0)),
            'high': float(k.get('h', 0)),
            'low': float(k.get('l', 0)),
            'close': float(k.get('c', 0)),
            'volume': float(k.get('v', 0)),
            'closed': k.get('x', False),
            'time': k.get('t', 0)
        }
        # Normalize symbol key: 'BTCUSDT' -> 'BTC' to match tickers and lookups
        base = symbol.replace('USDT', '').replace('BUSD', '')
        with self._lock:
            tf_list = self.klines[base][timeframe]
            if tf_list and tf_list[-1]['time'] == entry['time']:
                tf_list[-1] = entry
            else:
                tf_list.append(entry)
                if len(tf_list) > 2:
                    tf_list.pop(0)

    # ---- Connection ----

    def connect(self):
        url = "wss://stream.binance.com:9443/ws"
        self.ws = websocket.WebSocketApp(
            url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        self.ws_thread = threading.Thread(target=self.ws.run_forever, daemon=True)
        self.ws_thread.start()
        for _ in range(20):
            if self.is_running:
                break
            time.sleep(0.1)
        if self.is_running:
            self._send_subscribe(['!miniTicker@arr'])

    def _send_subscribe(self, streams: list):
        if not self.ws or not self.is_running:
            self._pending_subs.extend(streams)
            return
        msg = {"method": "SUBSCRIBE", "params": streams, "id": int(time.time() * 1000)}
        try:
            self.ws.send(json.dumps(msg))
            logger.info(f"Subscribed to {len(streams)} streams")
        except Exception as e:
            logger.error(f"Subscribe failed: {e}")
            self._pending_subs.extend(streams)

    def ensure_kline_streams(self, symbols: List[str], timeframes: List[str] = None, wait_seed: bool = False):
        """Subscribe to kline streams + REST-seed previous candle for instant data."""
        if timeframes is None:
            timeframes = ['5m', '15m', '30m', '1h']

        new_streams = []
        needs_seed = []  # (symbol, timeframe) pairs that need REST seeding

        for sym in symbols:
            base = sym.replace('/USDT', '').replace('/BUSD', '').lower()
            for tf in timeframes:
                key = f"{base}@kline_{tf}"
                if key not in self._kline_subs:
                    self._kline_subs.add(key)
                    new_streams.append(key)
                    needs_seed.append((sym, tf))

        if new_streams:
            self._send_subscribe(new_streams)
            if wait_seed:
                self._seed_klines_batch(needs_seed)
            else:
                self._executor.submit(self._seed_klines_batch, needs_seed)

    def _seed_klines_batch(self, items: list):
        """Fetch recent OHLCV via REST to seed kline cache for instant % change."""
        for sym, tf in items:
            try:
                since = None
                if tf == '1m':
                    since = int((time.time() - 180) * 1000)
                elif tf == '5m':
                    since = int((time.time() - 900) * 1000)
                elif tf == '15m':
                    since = int((time.time() - 2700) * 1000)
                elif tf == '30m':
                    since = int((time.time() - 5400) * 1000)
                else:
                    since = int((time.time() - 7200) * 1000)

                ohlcv = self.exchange.fetch_ohlcv(sym, tf, since=since, limit=2)
                if len(ohlcv) >= 2:
                    base = sym.replace('/USDT', '').replace('/BUSD', '')
                    with self._lock:
                        klist = self.klines[base][tf]
                        for candle in ohlcv:
                            entry = {
                                'open': float(candle[1]),
                                'high': float(candle[2]),
                                'low': float(candle[3]),
                                'close': float(candle[4]),
                                'volume': float(candle[5]),
                                'closed': True,
                                'time': candle[0]
                            }
                            # Don't duplicate entries
                            if not klist or klist[-1]['time'] != entry['time']:
                                klist.append(entry)
                            else:
                                klist[-1] = entry
                        # Keep only last 2
                        while len(klist) > 2:
                            klist.pop(0)
            except Exception as e:
                logger.debug(f"Seed kline failed for {sym} {tf}: {e}")

    def disconnect(self):
        self.is_running = False
        self._executor.shutdown(wait=False)
        if self.ws:
            self.ws.close()

    # ---- Data access ----

    def get_ticker(self, symbol: str) -> Optional[dict]:
        base = symbol.replace('/USDT', '').replace('/BUSD', '')
        with self._lock:
            return self.tickers.get(base)

    def get_all_tickers(self) -> Dict[str, dict]:
        with self._lock:
            return dict(self.tickers)

    def get_ticker_count(self) -> int:
        with self._lock:
            return len(self.tickers)

    def get_timeframe_change(self, symbol: str, timeframe: str) -> Optional[float]:
        base = symbol.replace('/USDT', '').replace('/BUSD', '')
        with self._lock:
            tf_klines = self.klines.get(base, {}).get(timeframe, [])
            if len(tf_klines) >= 2:
                prev = tf_klines[-2]['close']
                curr = tf_klines[-1]['close']
                if prev > 0:
                    return ((curr - prev) / prev) * 100
        return None

    def get_timeframe_changes(self, symbol: str, timeframes: List[str] = None) -> Dict:
        if timeframes is None:
            timeframes = ['5m', '15m', '30m', '1h']
        result = {}
        base = symbol.replace('/USDT', '').replace('/BUSD', '')
        with self._lock:
            for tf in timeframes:
                tf_klines = self.klines.get(base, {}).get(tf, [])
                if len(tf_klines) >= 2:
                    prev = tf_klines[-2]['close']
                    curr = tf_klines[-1]['close']
                    result[f'change_{tf}'] = ((curr - prev) / prev) * 100 if prev > 0 else None
                else:
                    result[f'change_{tf}'] = None
        return result

    def has_kline_data(self, symbol: str) -> bool:
        base = symbol.replace('/USDT', '').replace('/BUSD', '')
        with self._lock:
            return base in self.klines and len(self.klines[base]) > 0

    def get_top_volume_symbols(self, limit: int = 100) -> List[str]:
        with self._lock:
            major = Config.MAJOR_COINS
            tickers = [
                (sym, t.get('volume_24h', 0))
                for sym, t in self.tickers.items()
                if sym not in major and t.get('volume_24h', 0) > 0
            ]
            tickers.sort(key=lambda x: x[1], reverse=True)
            return [f"{sym}/USDT" for sym, _ in tickers[:limit]]


# ---- Singleton ----
_ws_service: Optional[BinanceWebSocketService] = None
_lock = threading.Lock()

def get_ws_service(api_key: str = '', api_secret: str = '') -> BinanceWebSocketService:
    global _ws_service
    with _lock:
        if _ws_service is None:
            _ws_service = BinanceWebSocketService(api_key, api_secret)
        return _ws_service

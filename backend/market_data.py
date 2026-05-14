import logging
import threading
import time
from typing import Dict, List, Optional
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import ccxt
from config import Config

logger = logging.getLogger(__name__)


class MarketDataService:
    """Binance REST-based market data with background polling + kline cache."""

    def __init__(self):
        self.exchange = ccxt.binance({
            'apiKey': '',
            'secret': '',
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'}
        })
        self.is_running = False
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=5)

        # Ticker cache: base -> {price, change_24h, volume_24h, ...}
        self.tickers: Dict[str, dict] = {}

        # Kline cache: base -> {timeframe -> (candles, fetched_at)}
        self.klines: Dict[str, Dict[str, tuple]] = defaultdict(dict)
        self.kline_ttl = 30  # seconds

        # Chart kline cache: base -> {timeframe -> [candles]} (more candles for charts)
        self.chart_klines: Dict[str, Dict[str, list]] = defaultdict(dict)

        self._stop_event = threading.Event()

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self._run_fetch_tickers()  # initial fetch
        threading.Thread(target=self._poll_loop, daemon=True).start()
        # Seed klines for top coins after first tickers arrive
        threading.Thread(target=self._initial_seed, daemon=True).start()
        logger.info("MarketDataService started (Binance REST)")

    def stop(self):
        self.is_running = False
        self._stop_event.set()
        self._executor.shutdown(wait=False)

    # ---- Background polling ----

    def _poll_loop(self):
        while not self._stop_event.is_set():
            self._stop_event.wait(10)
            if self._stop_event.is_set():
                break
            try:
                self._run_fetch_tickers()
            except Exception as e:
                logger.error(f"Ticker poll error: {e}")

    def _run_fetch_tickers(self):
        try:
            raw = self.exchange.fetch_tickers()
            filtered = {}
            for sym, t in raw.items():
                if not sym.endswith('/USDT:USDT'):
                    continue
                base = sym.split('/')[0]
                filtered[base] = {
                    'symbol': sym,
                    'name': base,
                    'price': t.get('last') or 0,
                    'change_24h': t.get('percentage') or 0,
                    'volume_24h': t.get('quoteVolume') or t.get('baseVolume') or 0,
                    'high_24h': t.get('high') or 0,
                    'low_24h': t.get('low') or 0,
                    'updated_at': time.time()
                }
            with self._lock:
                self.tickers = filtered
            logger.debug(f"Tickers updated: {len(filtered)} USDT pairs")
        except Exception as e:
            logger.error(f"fetch_tickers failed: {e}")

    def _initial_seed(self):
        time.sleep(3)  # wait for tickers
        top = self.get_top_volume_symbols(80)
        if top:
            logger.info(f"Seeding klines for {len(top)} coins...")
            self._fetch_klines_batch(top, ['1m', '5m', '15m', '30m', '1h'])
            logger.info("Kline seeding complete")
            # Also seed chart klines (more candles for chart display)
            self._seed_chart_klines(top[:30], ['5m'], 100)

    # ---- Kline fetching ----

    def _fetch_klines_batch(self, symbols: List[str], timeframes: List[str]):
        """Fetch klines via REST for multiple symbols x timeframes in parallel."""
        now = time.time()
        tasks = [(sym, tf) for sym in symbols for tf in timeframes]

        def fetch_one(sym, tf):
            try:
                since = self._since_for_timeframe(tf)
                ohlcv = self.exchange.fetch_ohlcv(sym, tf, since=since, limit=2)
                if len(ohlcv) >= 2:
                    base = sym.split('/')[0]
                    candles = [{
                        'open': float(c[1]),
                        'high': float(c[2]),
                        'low': float(c[3]),
                        'close': float(c[4]),
                        'volume': float(c[5]),
                        'closed': True,
                        'time': c[0]
                    } for c in ohlcv]
                    with self._lock:
                        self.klines[base][tf] = (candles, now)
            except Exception as e:
                logger.debug(f"Kline fetch failed {sym} {tf}: {e}")

        futures = [self._executor.submit(fetch_one, s, t) for s, t in tasks]
        for f in as_completed(futures):
            f.result()  # wait for all to complete

    def _seed_chart_klines(self, symbols: List[str], timeframes: List[str], limit: int = 100):
        """Fetch more klines for chart display and cache them."""
        def fetch_one(sym, tf):
            try:
                ohlcv = self.exchange.fetch_ohlcv(sym, tf, limit=limit)
                if len(ohlcv) >= 2:
                    base = sym.split('/')[0]
                    candles = [{
                        'time': c[0] // 1000,
                        'open': float(c[1]),
                        'high': float(c[2]),
                        'low': float(c[3]),
                        'close': float(c[4]),
                        'volume': float(c[5])
                    } for c in ohlcv]
                    with self._lock:
                        self.chart_klines[base][tf] = candles
                    logger.debug(f"Chart klines seeded: {base} {tf} ({len(candles)} candles)")
            except Exception as e:
                logger.debug(f"Chart kline seed failed {sym} {tf}: {e}")

        tasks = [(sym, tf) for sym in symbols for tf in timeframes]
        logger.info(f"Seeding chart klines for {len(tasks)} symbol/timeframe pairs...")
        futures = [self._executor.submit(fetch_one, s, t) for s, t in tasks]
        for f in as_completed(futures):
            f.result()

    @staticmethod
    def _since_for_timeframe(tf: str) -> int:
        now = int(time.time() * 1000)
        offsets = {'1m': 180, '5m': 900, '15m': 2700, '30m': 5400}
        offset = offsets.get(tf, 7200)
        return now - offset * 1000

    def ensure_kline_streams(self, symbols: List[str], timeframes: List[str] = None,
                             blocking: bool = False):
        """Fetch klines for symbols that need them. Non-blocking by default."""
        if timeframes is None:
            timeframes = ['1m', '5m', '15m', '30m', '1h']
        now = time.time()
        needs_fetch = []
        for sym in symbols:
            base = sym.split('/')[0]
            for tf in timeframes:
                cached = self.klines.get(base, {}).get(tf)
                if not cached or (now - cached[1]) > self.kline_ttl:
                    needs_fetch.append((sym, tf))
        if needs_fetch:
            unique_syms = list(set(s for s, _ in needs_fetch))
            unique_tfs = list(set(t for _, t in needs_fetch))
            if blocking:
                self._fetch_klines_batch(unique_syms, unique_tfs)
            else:
                self._executor.submit(self._fetch_klines_batch, unique_syms, unique_tfs)

    # ---- Data access ----

    def get_ticker(self, symbol: str) -> Optional[dict]:
        base = symbol.split('/')[0]
        with self._lock:
            return self.tickers.get(base)

    def get_all_tickers(self) -> Dict[str, dict]:
        with self._lock:
            return dict(self.tickers)

    def get_ticker_count(self) -> int:
        with self._lock:
            return len(self.tickers)

    def get_timeframe_change(self, symbol: str, timeframe: str) -> Optional[float]:
        base = symbol.split('/')[0]
        with self._lock:
            data = self.klines.get(base, {}).get(timeframe)
            if data:
                klines, _ = data
                if len(klines) >= 2:
                    prev = klines[-2]['close']
                    curr = klines[-1]['close']
                    if prev > 0:
                        return ((curr - prev) / prev) * 100
        return None

    def get_timeframe_changes(self, symbol: str, timeframes: List[str] = None) -> Dict:
        if timeframes is None:
            timeframes = ['5m', '15m', '30m', '1h']
        result = {}
        base = symbol.split('/')[0]
        with self._lock:
            for tf in timeframes:
                data = self.klines.get(base, {}).get(tf)
                if data:
                    klines, _ = data
                    if len(klines) >= 2:
                        prev = klines[-2]['close']
                        curr = klines[-1]['close']
                        result[f'change_{tf}'] = ((curr - prev) / prev) * 100 if prev > 0 else None
                    else:
                        result[f'change_{tf}'] = None
                else:
                    result[f'change_{tf}'] = None
        return result

    def has_kline_data(self, symbol: str) -> bool:
        base = symbol.split('/')[0]
        with self._lock:
            return base in self.klines and len(self.klines[base]) > 0

    def fetch_recent_klines(self, symbol: str, timeframe: str = '5m', limit: int = 100):
        """Fetch recent kline history for chart display. Uses cache when available."""
        base = symbol.split('/')[0]

        # 1. Try chart cache first (check freshness)
        cached = self.chart_klines.get(base, {}).get(timeframe)
        if cached and len(cached) >= limit:
            tf_seconds = {'1m': 60, '5m': 300, '15m': 900, '30m': 1800, '1h': 3600}.get(timeframe, 300)
            if cached[-1]['time'] >= time.time() - tf_seconds * 3:
                return cached[-limit:]

        # 2. Try regular kline cache (has time in ms, convert to s)
        reg = self.klines.get(base, {}).get(timeframe)
        if reg:
            candles, _ = reg
            if len(candles) >= limit:
                return [{
                    'time': c['time'] // 1000,
                    'open': c['open'], 'high': c['high'],
                    'low': c['low'], 'close': c['close'],
                    'volume': c['volume']
                } for c in candles]

        # 3. Live fetch from exchange (may fail behind firewall)
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            result = [{
                'time': c[0] // 1000,
                'open': float(c[1]),
                'high': float(c[2]),
                'low': float(c[3]),
                'close': float(c[4]),
                'volume': float(c[5])
            } for c in ohlcv]
            # Cache for future use
            with self._lock:
                self.chart_klines[base][timeframe] = result
            return result
        except Exception as e:
            logger.error(f"fetch_recent_klines live failed for {symbol} {timeframe}: {e}")
            return []

    def get_top_volume_symbols(self, limit: int = 100) -> List[str]:
        with self._lock:
            major = Config.MAJOR_COINS
            tickers = [
                (sym, t.get('volume_24h', 0))
                for sym, t in self.tickers.items()
                if sym not in major and t.get('volume_24h', 0) > 0
            ]
            tickers.sort(key=lambda x: x[1], reverse=True)
            return [f"{sym}/USDT:USDT" for sym, _ in tickers[:limit]]


# ---- Singleton ----
_service: Optional[MarketDataService] = None
_lock = threading.Lock()


def get_market_data() -> MarketDataService:
    global _service
    with _lock:
        if _service is None:
            _service = MarketDataService()
        return _service

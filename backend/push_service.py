import logging
import threading
import time

import requests

from config import Config
from market_data import get_market_data

logger = logging.getLogger(__name__)


class SignalPusher:
    """扫描异动标的（1 分钟 / 5 分钟涨跌幅超阈值，且 24h 成交量超阈值），推送到 ingest API。

    - 5 分钟：|涨跌幅| >= SIGNAL_5M_THRESHOLD（默认 2.0%），冷却 10 分钟
    - 1 分钟：|涨跌幅| >= SIGNAL_1M_THRESHOLD（默认 0.8%），冷却 5 分钟
    - 成交量门槛：SIGNAL_VOLUME_THRESHOLD（默认 5M）
    - 冷却：同标的 + 同周期独立冷却
    """

    def __init__(self):
        self._cooldown = {}  # (base, window) -> last pushed timestamp
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread = None
        self._specs = [
            ('5m', Config.SIGNAL_5M_THRESHOLD, Config.SIGNAL_5M_COOLDOWN_SECONDS),
            ('1m', Config.SIGNAL_1M_THRESHOLD, Config.SIGNAL_1M_COOLDOWN_SECONDS),
        ]

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._loop, daemon=True, name='signal-pusher')
        self._thread.start()
        logger.info("SignalPusher started (scan every %ds)", Config.SIGNAL_SCAN_INTERVAL)

    def stop(self):
        self._stop_event.set()

    def _loop(self):
        while not self._stop_event.is_set():
            try:
                self._scan()
            except Exception as e:
                logger.error(f"SignalPusher scan error: {e}")
            self._stop_event.wait(Config.SIGNAL_SCAN_INTERVAL)

    def _scan(self):
        md = get_market_data()
        tickers = md.get_all_tickers()

        candidates = []
        for base, t in tickers.items():
            vol = t.get('volume_24h') or 0
            if vol >= Config.SIGNAL_VOLUME_THRESHOLD:
                candidates.append((base, t))
        if not candidates:
            return

        # 确保候选标的的 K 线已就绪（非阻塞，首轮扫描仅预热缓存）
        timeframes = [tf for tf, _, _ in self._specs]
        symbols = [f"{base}/USDT:USDT" for base, _ in candidates]
        md.ensure_kline_streams(symbols, timeframes, blocking=False)

        now = time.time()
        pushed = 0
        for base, t in candidates:
            for tf, threshold, cooldown in self._specs:
                change = md.get_timeframe_change(f"{base}/USDT:USDT", tf)
                if change is None:
                    continue
                if abs(change) < threshold:
                    continue

                # 冷却检查（按 标的+周期 独立冷却）
                key = (base, tf)
                with self._lock:
                    last = self._cooldown.get(key, 0)
                    if now - last < cooldown:
                        continue
                    self._cooldown[key] = now

                direction = 'long' if change > 0 else 'short'
                payload = {
                    'symbol': base,
                    'window': tf,
                    'source': Config.INGEST_SOURCE,
                    'change_pct': round(change, 4),
                    'direction': direction,
                    'price': t.get('price'),
                    'ts': int(now * 1000),
                    'id': f"{base}-{tf}-{int(now)}-{direction}",
                }
                if self._post(payload):
                    pushed += 1
        if pushed:
            logger.info("SignalPusher pushed %d signal(s)", pushed)

    def _post(self, payload):
        if not Config.INGEST_TOKEN:
            logger.warning("SignalPusher: INGEST_TOKEN not set, skipping push")
            return False
        endpoint = 'price_5m' if payload.get('window') == '5m' else 'price_1m'
        url = f"{Config.INGEST_BASE_URL}/api/ingest/{endpoint}?token={Config.INGEST_TOKEN}"
        try:
            r = requests.post(url, json=payload, timeout=10)
            if r.status_code == 200:
                logger.debug(
                    "SignalPusher pushed %s %s (%+.2f%%): HTTP %s",
                    payload['symbol'], payload['window'], payload['change_pct'], r.status_code,
                )
                return True
            logger.warning(
                "SignalPusher push %s failed: HTTP %s %s",
                payload['symbol'], r.status_code, r.text[:200],
            )
        except Exception as e:
            logger.warning("SignalPusher push %s error: %s", payload['symbol'], e)
        return False


# ---- Singleton ----
_pusher = None
_pusher_lock = threading.Lock()


def get_signal_pusher() -> SignalPusher:
    global _pusher
    with _pusher_lock:
        if _pusher is None:
            _pusher = SignalPusher()
        return _pusher

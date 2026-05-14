import ccxt
import logging
from typing import List, Dict, Optional
from config import Config

logger = logging.getLogger(__name__)

class BinanceService:
    def __init__(self, api_key: str = '', api_secret: str = '', enable_rate_limit: bool = True):
        self.exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': enable_rate_limit,
            'options': {
                'defaultType': 'spot'
            }
        })
        
        self.major_coins = Config.MAJOR_COINS
        self.min_volume = Config.MIN_VOLUME_USD
        self.max_coins_limit = Config.MAX_COINS_LIMIT
        self.exclude_stablecoins = Config.EXCLUDE_STABLECOINS
    
    def is_altcoin(self, symbol: str) -> bool:
        base = symbol.replace('/USDT', '').replace('/BUSD', '')
        return base not in self.major_coins
    
    def is_stablecoin(self, symbol: str) -> bool:
        base = symbol.replace('/USDT', '').replace('/BUSD', '')
        stablecoins = {'USDT', 'USDC', 'BUSD', 'DAI', 'TUSD', 'USDP', 'FDUSD'}
        return base in stablecoins
    
    def fetch_all_tickers(self) -> List[Dict]:
        try:
            tickers = self.exchange.fetch_tickers()
            return tickers
        except Exception as e:
            logger.error(f"Error fetching tickers: {e}")
            return []
    
    def filter_altcoins(self, tickers: Dict, min_volume: float = None) -> List[Dict]:
        if min_volume is None:
            min_volume = self.min_volume
        
        altcoins = []
        
        for symbol, ticker in tickers.items():
            if not symbol.endswith('/USDT') and not symbol.endswith('/BUSD'):
                continue
            
            if not self.is_altcoin(symbol):
                continue
            
            if self.exclude_stablecoins and self.is_stablecoin(symbol):
                continue
            
            if 'last' not in ticker or ticker['last'] is None:
                continue
            
            volume = ticker.get('quoteVolume', 0)
            if volume < min_volume:
                continue
            
            altcoins.append({
                'symbol': symbol,
                'name': symbol.split('/')[0],
                'price': ticker['last'],
                'change_24h': ticker.get('percentage', 0),
                'change_1h': ticker.get('change', 0),
                'volume_24h': volume,
                'market_cap': ticker.get('marketCap', 0),
                'is_altcoin': True
            })
        
        if self.max_coins_limit and len(altcoins) > self.max_coins_limit:
            altcoins = altcoins[:self.max_coins_limit]
        
        return altcoins
    
    def get_top_gainers(self, altcoins: List[Dict], limit: int = 20) -> List[Dict]:
        sorted_coins = sorted(altcoins, key=lambda x: x['change_24h'], reverse=True)
        return sorted_coins[:limit]
    
    def get_top_losers(self, altcoins: List[Dict], limit: int = 20) -> List[Dict]:
        sorted_coins = sorted(altcoins, key=lambda x: x['change_24h'])
        return sorted_coins[:limit]
    
    def get_extreme_movers(self, altcoins: List[Dict], threshold: float = 10.0) -> Dict:
        gainers = [coin for coin in altcoins if coin['change_24h'] >= threshold]
        losers = [coin for coin in altcoins if coin['change_24h'] <= -threshold]
        
        return {
            'gainers': sorted(gainers, key=lambda x: x['change_24h'], reverse=True),
            'losers': sorted(losers, key=lambda x: x['change_24h'])
        }
    
    def get_timeframe_changes(self, symbol: str, timeframes: List[str] = ['5m', '15m', '30m']) -> Dict:
        try:
            changes = {}
            for tf in timeframes:
                ohlcv = self.exchange.fetch_ohlcv(symbol, tf, limit=2)
                if len(ohlcv) >= 2:
                    current_close = ohlcv[-1][4]
                    previous_close = ohlcv[-2][4]
                    change = ((current_close - previous_close) / previous_close) * 100
                    changes[f'change_{tf}'] = change
                else:
                    changes[f'change_{tf}'] = 0
            return changes
        except Exception as e:
            logger.error(f"Error fetching timeframe changes for {symbol}: {e}")
            return {f'change_{tf}': 0 for tf in timeframes}
    
    def get_timeframe_changes_rest(self, symbol: str, timeframes: List[str] = ['5m', '15m', '30m']) -> Dict:
        try:
            changes = {}
            for tf in timeframes:
                ohlcv = self.exchange.fetch_ohlcv(symbol, tf, limit=2)
                if len(ohlcv) >= 2:
                    current_close = ohlcv[-1][4]
                    previous_close = ohlcv[-2][4]
                    change = ((current_close - previous_close) / previous_close) * 100
                    changes[f'change_{tf}'] = change
                else:
                    changes[f'change_{tf}'] = 0
            return changes
        except Exception as e:
            logger.error(f"Error fetching timeframe changes for {symbol}: {e}")
            return {f'change_{tf}': 0 for tf in timeframes}
    
    def get_short_term_movers(self, altcoins: List[Dict], threshold: float = 5.0, 
                             volume_threshold: float = 5000000, limit: int = 50,
                             timeframe: str = '1h') -> Dict:
        movers = []
        for coin in altcoins:
            if coin['volume_24h'] < volume_threshold:
                continue
            
            try:
                ohlcv = self.exchange.fetch_ohlcv(coin['symbol'], timeframe, limit=2)
                if len(ohlcv) >= 2:
                    current_close = ohlcv[-1][4]
                    previous_close = ohlcv[-2][4]
                    change = ((current_close - previous_close) / previous_close) * 100
                    coin['short_term_change'] = change
                    
                    if abs(change) >= threshold:
                        movers.append(coin)
            except Exception as e:
                logger.error(f"Error fetching short term data for {coin['symbol']}: {e}")
                continue
        
        gainers = [coin for coin in movers if coin['short_term_change'] >= threshold]
        losers = [coin for coin in movers if coin['short_term_change'] <= -threshold]
        
        return {
            'gainers': sorted(gainers, key=lambda x: abs(x['short_term_change']), reverse=True)[:limit],
            'losers': sorted(losers, key=lambda x: abs(x['short_term_change']), reverse=True)[:limit]
        }
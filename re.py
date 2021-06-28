import requests
import time

def binance_util(symbol: str, timestamp: int)->str:
    base_url = 'https://api.binance.com/api/v3/klines'
    params = {
        'symbol': symbol,
        'interval': '1m',
        'startTime': timestamp-60000,
        'endTime': timestamp
    }
    re = requests.get(base_url, params)
    return re.url


def yahoo_util(tick: str, timestamp: int)->str:
    
import requests

def binance_util(symbol, timestamp):
    """
    :param symbol: ticker symbol on binance spot api
    :param timestamp: timestamp since Epoch in miliseconds
    :return: url for oracle request
    """
    path_filter = '$[-1:]..p'
    base_url = 'https://api.binance.com/api/v3/aggTrades'
    params = {
        'symbol': symbol,
        'startTime': timestamp-1000,
        'endTime': timestamp
    }
    re = requests.get(base_url, params)
    return re.url, path_filter

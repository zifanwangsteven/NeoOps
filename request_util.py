import time
import json
def utility():
    params = {}
    current = int(time.time() * 1000)
    MINUTE = 60 * 1000
    expiry = current + 5 * MINUTE
    threshold = expiry - 1
    base_url = 'https://api.binance.com/api/v3/aggTrades?symbol=BTCUSDT&startTime={}&endTime={}'.format(expiry-1000, expiry)
    params['pool_owner'] = 'NfT1orMtVTTDSPAJAGCutx6hFZkLKSr5dV'
    params['token_id'] = 1
    params['url'] = base_url
    params['json_filter'] = '$[-1:]..p'
    params['margin'] = 100000000
    params['expiry'] = expiry
    params['threshold'] = threshold
    params['stike'] = '35041.8'
    params['description'] = 'test'
    return json.dumps(params)

print(utility())

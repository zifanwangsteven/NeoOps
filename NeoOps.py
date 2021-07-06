from typing import Any, Dict, List, cast, Union
from boa3.builtin import CreateNewEvent, public, metadata, NeoMetadata, to_script_hash
from boa3.builtin.interop.blockchain import Transaction
from boa3.builtin.interop import Oracle
from boa3.builtin.contract import abort
from boa3.builtin.interop.contract import call_contract, destroy_contract, update_contract, GAS, NEO
from boa3.builtin.interop.runtime import calling_script_hash, script_container, check_witness, time, executing_script_hash
from boa3.builtin.interop.storage import delete, find, get, put
from boa3.builtin.type import UInt160, UInt256

#------------------------
# MANIFEST
#------------------------

@metadata
def manifest_metadata()->NeoMetadata:
    meta = NeoMetadata()
    meta.author = "StevenWang@Neo"
    meta.email = "wangzifansteven@gmail.com"
    meta.description = """Binary Options. With Crypto."""
    return meta


#-----------------------
# STORAGE KEYS
#-----------------------
OWNER_KEY = b'OWNER'
POOL_OWNER_KEY = b'pool_owner_'

# throughout this contract, the deployer of the smart contract will be consistently referred to as 'owner'
# while the owners of individual pools will be referred to as 'pool_owner's.

TOKEN_ACCEPTED_KEY = b'token_'
MARGIN_KEY = b'margin_'
TOTAL_MARGIN_KEY = b'total_margin_'
LONG_POSITION_KEY = b'long_'
SHORT_POSITION_KEY = b'short_'
URL_KEY = b'url_'
FILTER_KEY = b'filter_'
RAW_DATA_KEY = b'raw_data_'
EXPIRY_KEY = b'expiry_'
SYMBOL_KEY = b'symbol_'
DESCRIPTION_KEY = b'description_'
THRESHOLD_KEY = b'threshold_'
PLAYER_POSITION_KEY = b'user_bet_'
RESULT_KEY = b'result_'
STATUS_KEY = b'status_' # 0 for open; 1 for canceled; 2 for closed
DEPOSIT_KEY = b'deposit_'
STRIKE_PRICE_KEY = b'strike_'

OWNER_COMMISSION = 1 # 0.1%
POOL_OWNER_COMMISSION = 2 # 0.2%
DEPOSIT_COMMISSION = 2 # 0.2%
CANCEL_PENALTY = 3 # 0.3%
MINIMUM_DEPOSIT = 1 * 100_000_000 # minimum deposit for creating a pool
ORACLE_ADDRESS = 'NTz4UrybSL4C7HSfaVpXV6hcsWTkks8Nrj'

NEO_ADDRESS = NEO
GAS_ADDRESS = GAS


#-----------------------
# CONTRACT LOGIC
#-----------------------

@public
def pool_init(pool_owner: UInt160, token_id: int, url: str, json_filter: str, margin: int, expiry: int, threshold: int, deposit: int, strike: str, description: str)-> UInt256:

    if not check_witness(pool_owner):
        raise Exception('No authorization.')
    tx: Transaction = script_container
    pool_id: UInt256 = tx.hash
    put(POOL_OWNER_KEY + pool_id, pool_owner)

    if token_id == 0:
        put(TOKEN_ACCEPTED_KEY + pool_id, NEO_ADDRESS)
    elif token_id == 1:
        put(TOKEN_ACCEPTED_KEY + pool_id, GAS_ADDRESS)
    else:
        raise Exception('Unauthorized token.')

    if deposit < MINIMUM_DEPOSIT:
        raise Exception('Mininum deposit is 1 GAS token.')
    transfer_token(GAS, pool_owner, executing_script_hash, deposit, None)
    put(DEPOSIT_KEY + pool_id, deposit)

    put(URL_KEY + pool_id, url)
    put(FILTER_KEY + pool_id, json_filter)

    if margin < 0:
        raise Exception('Margin must an integer greater than 0.')
    put(MARGIN_KEY + pool_id ,margin)

    if expiry < time:
        raise Exception('Expiry time is set too soon.')
    put(EXPIRY_KEY + pool_id, expiry)

    if threshold < time:
        raise Exception('Threshold time is set too soon.')

    if threshold >= expiry:
        raise Exception('Threshold time must be set before expiry time.')
    put(THRESHOLD_KEY + pool_id, threshold)

    put(STRIKE_PRICE_KEY + pool_id, strike)

    put(DESCRIPTION_KEY + pool_id, description)

    put(LONG_POSITION_KEY + pool_id, 0)
    put(SHORT_POSITION_KEY + pool_id, 0)
    put(TOTAL_MARGIN_KEY + pool_id, 0)

    put(STATUS_KEY + pool_id, 0)
    return pool_id

@public
def retrieve_pool(pool_id: UInt256)-> Dict:
    pool_owner = get(POOL_OWNER_KEY + pool_id)
    if len(pool_owner) == 0:
        raise Exception("Pool doesn't exist.")
    json = {}
    json['pool_owner'] = UInt160(pool_owner)
    json['expiry'] = get(EXPIRY_KEY + pool_id).to_int()
    json['token_id'] = UInt160(get(TOKEN_ACCEPTED_KEY + pool_id))
    json['margin'] = get(MARGIN_KEY + pool_id).to_int()
    json['total_margin'] = get(TOTAL_MARGIN_KEY + pool_id).to_int()
    json['short'] = get(SHORT_POSITION_KEY + pool_id).to_int()
    json['long'] = get(LONG_POSITION_KEY + pool_id).to_int()
    json['url'] = get(URL_KEY + pool_id).to_str()
    json['filter'] = get(FILTER_KEY + pool_id).to_str()
    json['description'] = get(DESCRIPTION_KEY + pool_id).to_str()
    json['status'] = get(STATUS_KEY + pool_id).to_int()
    json['deposit'] = get(DEPOSIT_KEY + pool_id).to_int()
    json['strike_price'] = get(STRIKE_PRICE_KEY + pool_id).to_str()
    json['result'] = get(RESULT_KEY + pool_id).to_int()
    json['raw'] = get(RAW_DATA_KEY + pool_id).to_str()
    return json

@public
def list_ongoing_pool()->Dict:
    pools = find(POOL_OWNER_KEY)
    json = {}
    while pools.next():
        result_pair = pools.value
        storage_key = cast(bytes, result_pair[0])
        pool_id = UInt256(storage_key[len(POOL_OWNER_KEY):])
        if get(STATUS_KEY + pool_id).to_int() == 0:
            json[pool_id.to_str()] = retrieve_pool(pool_id)
    return json



@public
def cancel_pool(pool_id: UInt256):
    pool_owner = get(POOL_OWNER_KEY + pool_id)
    if len(pool_owner) == 0:
        raise Exception('Pool does not exist.')

    pool_owner = UInt160(pool_owner)
    if not check_witness(pool_owner):
        raise Exception('No authorization.')

    if get(STATUS_KEY + pool_id).to_int() != 0:
        raise Exception('Pool already canceled or closed.')

    token = UInt160(get(TOKEN_ACCEPTED_KEY + pool_id))
    margin = get(MARGIN_KEY + pool_id).to_int()

    players = find(PLAYER_POSITION_KEY + pool_id)
    while players.next():
        pair = players.value
        storage_key = cast(bytes, pair[0])
        address = UInt160(storage_key[len(PLAYER_POSITION_KEY + pool_id):])
        transfer_token(token, executing_script_hash, address, margin, None)

    put(STATUS_KEY + pool_id, 1)

@public
def bet(player: UInt160, pool_id: UInt256, bet_option: int):

    if len(get(POOL_OWNER_KEY+pool_id)) == 0:
        raise Exception("Pool does not exist.")

    if not check_witness(player):
        raise Exception("No authorization.")

    if get(STATUS_KEY + pool_id).to_int() != 0:
        raise Exception("Pool already canceled or closed.")

    threshold = get(THRESHOLD_KEY + pool_id).to_int()
    if time > threshold:
        raise Exception('Already passed betting threshold.')

    if len(get(PLAYER_POSITION_KEY + pool_id + player)) != 0:
        raise Exception("Position already settled.")

    if bet_option != 0 and bet_option != 1:
        raise Exception("Bet option must be either 1 (Long) or 0 (Short).")

    margin: int = get(MARGIN_KEY + pool_id).to_int()
    total_margin: int = get(TOTAL_MARGIN_KEY + pool_id).to_int()
    token = UInt160(get(TOKEN_ACCEPTED_KEY + pool_id))
    transfer_token(token, player, executing_script_hash, margin, None)

    if bet_option == 0:
        total_short: int = get(SHORT_POSITION_KEY + pool_id).to_int()
        total_short += 1
        put(SHORT_POSITION_KEY + pool_id, total_short)
    else:
        total_long: int = get(LONG_POSITION_KEY + pool_id).to_int()
        total_long += 1
        put(LONG_POSITION_KEY + pool_id, total_long)

    total_margin += margin
    put(TOTAL_MARGIN_KEY + pool_id, total_margin)
    put(PLAYER_POSITION_KEY + pool_id + player, bet_option)


@public
def cancel_bet(player: UInt160, pool_id: UInt256):
    if len(get(POOL_OWNER_KEY+pool_id)) == 0:
        raise Exception("Pool does not exist.")

    if not check_witness(player):
        raise Exception('No authorization.')

    if len(get(PLAYER_POSITION_KEY + pool_id + player)) == 0:
        raise Exception('No position settled in current pool.')

    if get(STATUS_KEY + pool_id).to_int() != 0:
        raise Exception('Pool already canceled or closed.')

    margin: int = get(MARGIN_KEY+pool_id).to_int()
    total_margin: int = get(TOTAL_MARGIN_KEY+pool_id).to_int()
    refund = margin - margin * CANCEL_PENALTY // 1000
    total_margin -= margin
    put(TOTAL_MARGIN_KEY + pool_id, total_margin)
    position:int = get(PLAYER_POSITION_KEY + pool_id + player).to_int()
    token = UInt160(get(TOKEN_ACCEPTED_KEY + pool_id))
    transfer_token(token, executing_script_hash, player, refund, None)

    if position == 0:
        total_short: int = get(SHORT_POSITION_KEY + pool_id).to_int()
        total_short -= 1
        put(SHORT_POSITION_KEY + pool_id, total_short)
    else:
        total_long: int = get(LONG_POSITION_KEY + pool_id).to_int()
        total_long -= 1
        put(LONG_POSITION_KEY + pool_id, total_long)

    delete(PLAYER_POSITION_KEY + pool_id + player)

@public
def oracle_call(pool_id: UInt256):
    pool_owner = get(POOL_OWNER_KEY + pool_id)
    if len(pool_owner) == 0:
        raise Exception('Pool does not exist.')

    pool_owner = UInt160(pool_owner)
    if not check_witness(pool_owner):
        raise Exception('No authorization.')

    if get(STATUS_KEY + pool_id).to_int() != 0:
        raise Exception('Pool already canceled or closed.')

    expiry = get(EXPIRY_KEY + pool_id).to_int()
    if time < expiry:
        raise Exception('Not yet time to call on oracle.')

    url = get(URL_KEY + pool_id).to_str()
    json_filter = get(FILTER_KEY + pool_id).to_str()
    Oracle.request(url, json_filter, 'store', pool_id, 100000000)


@public
def store(url: str, user_data: Any, code: int, result: bytes):
    oracle_hash = ORACLE_ADDRESS.to_script_hash()
    if calling_script_hash != oracle_hash:
        raise Exception('No authorization')
    pool_id = cast(UInt160, user_data)
    spot = cast(str, result)
    spot = spot[2 : -2]
    if code != 0:
        put(RAW_DATA_KEY + pool_id, 'Error')
    else:
        put(RAW_DATA_KEY + pool_id, spot)

def greater_equal(a: str, b: str)->bool:
    length_a = len(a)
    length_b = len(b)
    decimal_a: int = 0
    decimal_b: int = 0
    i: int = 0
    while i < length_a:
        if a[i] == '.':
            decimal_a = i
            break
        i += 1
    if decimal_a == 0:
        decimal_a = length_a
    i = 0
    while i < length_b:
        if b[i] == '.':
            decimal_b = i
            break
        i += 1
    if decimal_b == 0:
        decimal_b = length_b
    if decimal_a > decimal_b:
        return True
    elif decimal_a < decimal_b:
        return False
    else:
        for i in range(0, decimal_a):
            if a[i] > b[i]:
                return True
            elif a[i] < b[i]:
                return False
            i+=1
        for i in range(decimal_a+1, min(length_a, length_b)):
            if a[i] > b[i]:
                return True
            elif a[i] < b[i]:
                return False
        if length_a >= length_b:
            return True
        else:
            return False
    return False

@public
def payout(pool_id: UInt256):
    pool_owner = get(POOL_OWNER_KEY + pool_id)
    if len(pool_owner) == 0:
        raise Exception('Pool does not exist.')

    pool_owner = UInt160(pool_owner)
    if not check_witness(pool_owner):
        raise Exception("No authorization.")

    if get(STATUS_KEY + pool_id).to_int() != 0:
        raise Exception('Pool already canceled or closed.')

    spot = get(RAW_DATA_KEY + pool_id)
    if len(spot) == 0:
        raise Exception('Spot price not yet retrieved by Oracle nodes.')

    strike = get(STRIKE_PRICE_KEY + pool_id)
    spot = cast(str, spot)
    strike = cast(str, strike)

    if greater_equal(spot, strike):
        result = 1
    else:
        result = 0
    put(RESULT_KEY + pool_id, result)

    owner = UInt160(get(OWNER_KEY))
    token = UInt160(get(TOKEN_ACCEPTED_KEY + pool_id))
    players = find(PLAYER_POSITION_KEY + pool_id)
    total_short = get(SHORT_POSITION_KEY + pool_id).to_int()
    total_long = get(LONG_POSITION_KEY + pool_id).to_int()
    total_margin = get(TOTAL_MARGIN_KEY + pool_id).to_int()

    # settles commission derived from players' margin pool
    owner_commission = total_margin * OWNER_COMMISSION // 1000
    transfer_token(token, executing_script_hash, owner, owner_commission, None)
    pool_owner_commission = total_margin * POOL_OWNER_COMMISSION // 1000
    transfer_token(token, executing_script_hash, pool_owner, pool_owner_commission, None)
    total_margin -= (owner_commission + pool_owner_commission)

    # settles commission derived from deposit
    deposit = get(DEPOSIT_KEY + pool_id).to_int()
    deposit_commission = deposit * DEPOSIT_COMMISSION // 1000
    deposit -= deposit_commission
    transfer_token(token, executing_script_hash, pool_owner, deposit, None)

    if result == 0 and total_short != 0:
        payoff = total_margin // total_short
        while players.next():
            pair = players.value
            storage_key = cast(bytes, pair[0])
            position = cast(int, pair[1])
            if position == 0:
                address = UInt160(storage_key[len(PLAYER_POSITION_KEY + pool_id):])
                transfer_token(token, executing_script_hash, address, payoff, None)

    if result == 1 and total_long != 0:
        payoff = total_margin // total_long
        while players.next():
            pair = players.value
            storage_key = cast(bytes, pair[0])
            position = cast(int, pair[1])
            if position == 1:
                address = UInt160(storage_key[len(PLAYER_POSITION_KEY + pool_id):])
                transfer_token(token, executing_script_hash, address, payoff, None)

    put(STATUS_KEY + pool_id, 2)



def transfer_token(token_id: UInt160, from_address: UInt160, to_address: UInt160, amount: int, data: Any):
    success: bool = call_contract(token_id, 'transfer', [from_address, to_address, amount, data])
    if not success:
        raise Exception('Transfer of token was not successful.')

@public
def onNEP17Payment(from_address: UInt160, amount: int, data: Any):
    pass


#-----------------------
# CONTRACT MANAGEMENT
#-----------------------

@public
def _deploy(data: Any, update: bool):
    if update:
        return
    if len(get(OWNER_KEY)) != 0:
        return
    put(OWNER_KEY, "NfT1orMtVTTDSPAJAGCutx6hFZkLKSr5dV".to_script_hash())


@public
def update(script: bytes, manifest: bytes):
    owner = UInt160(get(OWNER_KEY))
    if not check_witness(owner):
        raise Exception('No authorization.')

    update_contract(script, manifest)


@public
def destroy():
    owner = UInt160(get(OWNER_KEY))
    if not check_witness(owner):
        raise Exception('No authorization.')

    destroy_contract()

from typing import Any, Dict, List, cast
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
    meta.description = """
        One stop margin pooling game.
    """
    return meta


#-----------------------
# EVENT
#-----------------------



#-----------------------
# STORAGE KEYS
#-----------------------
OWNER_KEY = b'OWNER'
POOL_OWNER_KEY = b'pool_owner_'
TOKEN_ACCEPTED_KEY = b'token_'
MARGIN_KEY = b'margin_'
TOTAL_MARGIN_KEY = b'total_margin_'
LONG_POSITION_KEY = b'long_'
SHORT_POSITION_KEY = b'short_'
URL_KEY = b'url_'
FILTER_KEY = b'filter_'
RAW_DATA_KEY = b'raw_data_'
EXPIRY_KEY = b'expiry_'
DESCRIPTION_KEY = b'description_'
PLAYER_POSITION_KEY = b'user_bet_'
RESULT_KEY = b'result_'
DEPOSIT_KEY = b'deposit_'
STRIKE_PRICE_KEY = b'strike_'

OWNER_COMMISSION = 1 # 0.1%
POOL_OWNER_COMMISSION = 2 # 0.2%
MINIMUM_DEPOSIT = 10 * 10_000_000 # minimum deposit for creating a pool

#-----------------------
# CONTRACT LOGIC
#-----------------------

@public
def pool_init(owner: UInt160, token_id: UInt256, url: str, json_filter: str, margin: int, expiry: int, description: str)-> UInt256:
    if not check_witness(owner):
        raise Exception('No authorization.')
    tx: Transaction = script_container
    pool_id: UInt256 = tx.hash
    put(POOL_OWNER_KEY + pool_id, owner)
    # need to check validity of token_id
    put(TOKEN_ACCEPTED_KEY + pool_id, token_id)
    # need to check validity of url
    put(URL_KEY + pool_id, url)
    # need to check validity of filter
    put(FILTER_KEY + pool_id, json_filter)
    assert margin > 0
    put(MARGIN_KEY + pool_id ,margin)
    assert expiry > time
    put(EXPIRY_KEY + pool_id, expiry)
    put(DESCRIPTION_KEY + pool_id, description)
    put(LONG_POSITION_KEY + pool_id, 0)
    put(SHORT_POSITION_KEY + pool_id, 0)
    # do we need to fire an event here?
    # do we need to issue an extra transaction requiring gas to be transferred?
    return pool_id

@public
def retrieve_pool(pool_id: UInt256)-> List:
    pool_owner = get(POOL_OWNER_KEY + pool_id)
    if len(pool_owner) == 0:
        raise Exception("Pool doesn't exist.")
    pool_owner = UInt160(pool_owner)
    expiry = get(EXPIRY_KEY + pool_id).to_int()
    token_id = UInt160(get(TOKEN_ACCEPTED_KEY + pool_id))
    margin = get(MARGIN_KEY + pool_id).to_int()
    total_margin = get(TOTAL_MARGIN_KEY + pool_id).to_int()
    short = get(SHORT_POSITION_KEY + pool_id).to_int()
    long = get(LONG_POSITION_KEY + pool_id).to_int()
    url = get(URL_KEY + pool_id).to_str()
    json_filter = get(FILTER_KEY + pool_id).to_str()
    description = get(DESCRIPTION_KEY + pool_id).to_str()
    return [pool_id, pool_owner, expiry, token_id, margin, total_margin, short, long ,url ,json_filter, description]


@public
def cancel_pool(pool_id: UInt256)-> List:
    pass




@public
def bet(player: UInt160, pool_id: UInt256, bet_option: int):
    if len(get(POOL_OWNER_KEY+pool_id)) == 0:
        raise Exception("Pool does not exist.")
    if len(get(DEPOSIT_KEY + pool_id)) == 0:
        raise Exception("Pool not yet available for bet.")
    if not check_witness(player):
        raise Exception("No authorization.")
    if len(get(RESULT_KEY + pool_id)) != 0:
        raise Exception("Pool already closed.")
    if len(get(PLAYER_POSITION_KEY + pool_id + player)) == 0:
        raise Exception("Position already settled.")
    if bet_option != 0 and bet_option != 1:
        raise Exception("Bet option must be either 1 (Long) or 0 (Short).")
    margin: int = get(MARGIN_KEY + pool_id).to_int()
    total_margin: int = get(TOTAL_MARGIN_KEY + pool_id).to_int()

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
    # check type casting
    transfer_token(UInt160(get(TOKEN_ACCEPTED_KEY + pool_id)), player, executing_script_hash, margin, ['bet', UInt256])
    put(PLAYER_POSITION_KEY + pool_id + player, bet_option)
    # fire an event?

@public
def cancel_bet(player: UInt160, pool_id: UInt256):
    if not check_witness(player):
        raise Exception('No authorization.')
    if len(get(PLAYER_POSITION_KEY + pool_id + player)) == 0:
        raise Exception('No position settled in current pool.')
    if len(get(RESULT_KEY + pool_id)) != 0:
        raise Exception('Contract already settled.')
    margin: int = get(MARGIN_KEY+pool_id).to_int()
    total_margin: int = get(TOTAL_MARGIN_KEY+pool_id).to_int()
    refund = margin - margin * 3 // 100 # 3% penalty
    total_margin -= refund
    put(TOTAL_MARGIN_KEY + pool_id, total_margin)
    position:int = get(PLAYER_POSITION_KEY + pool_id + player).to_int()
    if position == 0:
        total_short: int = get(SHORT_POSITION_KEY + pool_id).to_int()
        total_short -= 1
        put(SHORT_POSITION_KEY + pool_id, total_short)
    else:
        total_long: int = get(LONG_POSITION_KEY + pool_id).to_int()
        total_long -= 1
        put(LONG_POSITION_KEY + pool_id, total_long)
    transfer_token(cast(UInt160, get(TOKEN_ACCEPTED_KEY + pool_id)), executing_script_hash, player, refund, ['refund', pool_id])

    delete(PLAYER_POSITION_KEY + pool_id + player)

@public
def oracle_call(pool_id: UInt160):
    owner: UInt160 = UInt160(get(POOL_OWNER_KEY + pool_id))
    if not check_witness(owner):
        raise Exception('No authorization.')
    expiry = get(EXPIRY_KEY + pool_id).to_int()
    if time < expiry:
        raise Exception('Not yet time to call on oracle.')
    url = get(URL_KEY + pool_id).to_str()
    json_filter = get(FILTER_KEY + pool_id).to_str()
    Oracle.request(url, json_filter, pool_id.to_str(), 'store', 1_00000000)


# @public
# def store(url: str, user_data: Any, code: int, result: bytes) -> None:
#     pool_id = UInt160(user_data)
#     # questionable
#     if code != 0:
#         put(RAW_DATA_KEY + pool_id, 'Error')
#     else:
#         put(RAW_DATA_KEY + pool_id, result)

@public
def interpret(pool_id: UInt256):
    owner = get(POOL_OWNER_KEY + pool_id)
    if(len(owner)) == 0:
        raise Exception('Pool does not exist.')
    owner = UInt160(owner)
    if not check_witness(owner):
        raise Exception('No authorization.')
    strike = get(STRIKE_PRICE_KEY + pool_id).to_double()
    spot = get(RAW_DATA_KEY + pool_id).to_double()
    if spot >= strike:
        put(RESULT_KEY + pool_id, 1)
    else:
        put(RESULT_KEY + pool_id, 0)

@public
def payout(pool_id: UInt256):
    pool_owner = UInt160(get(POOL_OWNER_KEY + pool_id))
    if not check_witness(pool_owner):
        raise Exception("No authorization.")
    if len(get(RESULT_KEY + pool_id)) == 0:
        raise Exception("Result not yet available")
    owner = UInt160(get(OWNER_KEY))
    token = UInt160(get(TOKEN_ACCEPTED_KEY + pool_id))
    players = find(PLAYER_POSITION_KEY + pool_id)
    result = get(RESULT_KEY + pool_id).to_int()
    total_short = get(SHORT_POSITION_KEY + pool_id)
    total_long = get(LONG_POSITION_KEY + pool_id).to_int()
    total_margin = get(TOTAL_MARGIN_KEY + pool_id).to_int()
    owner_commission = total_margin * OWNER_COMMISSION // 1000
    transfer_token(token, executing_script_hash, owner, owner_commission)
    pool_owner_commission = total_margin * POOL_OWNER_COMMISSION // 1000
    transfer_token(token, executing_script_hash, pool_owner, pool_owner_commission)
    total_margin -= (owner_commission + pool_owner_commission)
    if result == 0:
        payoff = total_margin // total_short
        while players.next():
            pair = players.value
            storage_key = pair[0]
            position = pair[1].to_int()
            if position == 0:
                address = UInt160(storage_key[len(PLAYER_POSITION_KEY + pool_id):])
                transfer_token(token, executing_script_hash, address, payoff)
    else:
        payoff = total_margin // total_long
        while players.next():
            pair = players.value
            storage_key = pair[0]
            position = pair[1].to_int()
            if position == 1:
                address = UInt160(storage_key[len(PLAYER_POSITION_KEY + pool_id):])
                transfer_token(token, executing_script_hash, address, payoff)



@public
def transfer_token(token_id: UInt160, from_address: UInt160, to_address: UInt160, amount: int, data: [str, UInt256]):
    # check is token_id is valid
    success: bool = call_contract(token_id, 'transfer', [from_address, to_address, amount, data])
    if not success:
        raise Exception('Transfer of token was not successful.')

@public
def onNEP17Payment(from_address: UInt160, amount: int, data: [str, UInt256]):
    if data[0] == 'deposit':
        owner = get(POOL_OWNER_KEY + data[1])
        if len(owner) == 0:
            abort()
        elif from_address != UInt160(owner):
            abort()
        elif calling_script_hash != GAS:
            abort()
        elif amount < MINIMUM_DEPOSIT:
            abort()
        else:
            put(DEPOSIT_KEY + data[1], amount)

    elif data[0] == 'bet' or data[0] == 'refund':
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
    put(OWNER_KEY, "FILL IN ADDRESS HERE".to_script_hash())


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

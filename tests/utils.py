from typing import Tuple, List, Dict, Any, Union
from enum import Enum

import base64
import time
import datetime
from math import ceil, log
from neo3.core.types import UInt160, UInt256


class HashStr(str):
    def __init__(self, string: str):
        super(HashStr, self).__init__()
        # check length of string here
        # assert string.startswith('0x')
        self.string = string

    def to_str(self):
        return self.string

    def __str__(self):
        return self.string

    def __repr__(self):
        return self.string


class Hash256Str(HashStr):
    """
    0x59916d8c2fc5feb06b77aec289ac34b49ae3bccb1f88fe64ea5172c79fc1af05
    """

    def __init__(self, string: str):
        # assert string.startswith('0x')
        if len(string) == 64:
            string = '0x' + string
        assert len(string) == 66
        super().__init__(string)

    @classmethod
    def from_UInt256(cls, u: UInt256):
        u_bytearray = bytearray(u._data)
        u_bytearray.reverse()
        hash256str = u_bytearray.hex()
        return cls(hash256str)


class Hash160Str(HashStr):
    """
    0xf61eebf573ea36593fd43aa150c055ad7906ab83
    """

    def __init__(self, string: str):
        # assert string.startswith('0x')
        if len(string) == 40:
            string = '0x' + string
        assert len(string) == 42
        super().__init__(string)

    @classmethod
    def from_UInt160(cls, u: UInt160):
        u_bytearray = bytearray(u._data)
        u_bytearray.reverse()
        hash160str = u_bytearray.hex()
        return cls(hash160str)

    def to_UInt160(self):
        return UInt160.from_string(self.string)


def gen_expiry_timestamp_and_str(days: int) -> Tuple[int, str]:
    today = datetime.date.today()
    days_later = today + datetime.timedelta(days=days)
    days_later_ending_milisecond = (int(time.mktime(time.strptime(str(days_later), '%Y-%m-%d')) + 86400) * 1000 - 1)
    days_later_date_str = days_later.strftime('%m_%d_%Y')
    return days_later_ending_milisecond, days_later_date_str


def gen_expiry_timestamp_and_str_in_seconds(seconds: int) -> Tuple[int, str]:
    current_time = time.time()
    today = datetime.date.fromtimestamp(current_time)
    seconds_later = today + datetime.timedelta(seconds=seconds)
    seconds_later_date_str = seconds_later.strftime('%m_%d_%Y') + str(ceil(current_time)+seconds)
    return ceil((current_time + seconds) * 1000), seconds_later_date_str


class WitnessScope(Enum):
    NONE = 'None'
    CalledByEntry = 'CalledByEntry'
    CustomContracts = 'CustomContracts'
    CustomGroups = 'CustomGroups'
    Global = 'Global'


class Signer:
    def __init__(self, account: Hash160Str, scopes: WitnessScope = WitnessScope.CalledByEntry,
                 allowedcontracts: List[Hash160Str] = None, allowedgroups: List[str] = None):
        self.account: Hash160Str = account
        self.scopes: WitnessScope = scopes
        if allowedcontracts == None:
            allowedcontracts = []
        self.allowedcontracts = [str(allowedcontract) for allowedcontract in allowedcontracts]
        if allowedgroups == None:
            allowedgroups = []
        self.allowedgroups = allowedgroups

    def to_dict(self):
        return {
            'account': str(self.account),
            'scopes': self.scopes.value,
            'allowedcontracts': self.allowedcontracts,
            'allowedgroups': self.allowedgroups,
        }


class ResultInterpreter:
    @staticmethod
    def bytes_to_int(bytes_: bytes):
        return int.from_bytes(bytes_, byteorder='little', signed=False)

    @staticmethod
    def bytes_to_Hash160str(bytestring: bytes):
        return Hash160Str.from_UInt160(UInt160.deserialize_from_bytes(bytestring))

    @staticmethod
    def int_to_bytes(int_: int, bytes_needed: int = None):
        if not bytes_needed:
            bytes_needed = int(log(int_, 256)) + 1  # may be not accurate
        try:
            return int_.to_bytes(bytes_needed, 'little')
        except OverflowError:
            return int_.to_bytes(bytes_needed + 1, 'little')


class EngineResultInterpreter(ResultInterpreter):
    @staticmethod
    def interpret_getCollaterals(collaterals: Dict[bytes, bytes]) -> Dict[Hash160Str, int]:
        result_dict = dict()
        len_collaterals = len(b'collaterals')
        for k, v in zip(collaterals.keys(), collaterals.values()):
            result_dict[EngineResultInterpreter.bytes_to_Hash160str(k[len_collaterals:])] = EngineResultInterpreter.bytes_to_int(v)
        return result_dict

    @staticmethod
    def interpret_getPairsMap(pairsMap: Dict[bytes, bytes]) -> Dict[int, Hash160Str]:
        pairs = dict()
        for k, v in zip(pairsMap.keys(), pairsMap.values()):
            paired_token_address_bytes = k[(len(b'pairs') + 21):]
            pairs[EngineResultInterpreter.bytes_to_int(v)] \
                = EngineResultInterpreter.bytes_to_Hash160str(paired_token_address_bytes)
        return pairs

    @staticmethod
    def interpret_getPairAttribtutes(Pair: Dict[bytes, bytes]) -> Dict[str, Any]:
        pair_attributes = dict()
        for k, v in zip(Pair.keys(), Pair.values()):
            attribute_name = k.split(b'_')[2].decode()
            if 'Token' in attribute_name:
                attribute_value = EngineResultInterpreter.bytes_to_Hash160str(v)
            else:
                attribute_value = ClientResultInterpreter.bytes_to_int(v)
            pair_attributes[attribute_name] = attribute_value
        return pair_attributes


class ClientResultInterpreter(ResultInterpreter):
    @staticmethod
    def interpret_raw_result_as_iterator(result):
        return result['result']['stack'][0]['iterator']

    @staticmethod
    def base64_struct_to_bytestrs(base64_struct: dict) -> List[bytes]:
        processed_struct = []
        if type(base64_struct) is dict and 'type' in base64_struct and base64_struct['type'] == 'Struct':
            values = base64_struct['value']
            for value in values:
                if value['type'] == 'ByteString':
                    processed_struct.append(base64.b64decode(value['value']))
        return processed_struct

    @staticmethod
    def interpret_getCollaterals(collaterals:dict) -> List:
        return [ClientResultInterpreter.bytes_to_Hash160str(collateral[len(b'collaterals'):]) for collateral in collaterals]

    @staticmethod
    def interpret_getPairsMap(Pairs:dict) -> Dict[int, Dict]:
        pairs = dict()
        for k, v in zip(Pairs.keys(), Pairs.values()):
            paired_token_info_bytes = k[(len(b'pairs')):]
            collateral_token_address, paired_token_address, paired_token_expiry, paired_token_mintRatio = paired_token_info_bytes.split(b'_')
            pairs[ClientResultInterpreter.bytes_to_int(v)] = {
                'collateralToken': ClientResultInterpreter.bytes_to_Hash160str(collateral_token_address),
                'pairedToken': ClientResultInterpreter.bytes_to_Hash160str(paired_token_address),
                'expiry': ClientResultInterpreter.bytes_to_int(paired_token_expiry),
                'mintRatio': ClientResultInterpreter.bytes_to_int(paired_token_mintRatio)
            }
        return pairs

    @staticmethod
    def interpret_getFeesMap(fees: dict) -> Dict[Hash160Str, int]:
        fees_dict = dict()
        for k, v in zip(fees.keys(), fees.values()):
            fees_dict[ClientResultInterpreter.bytes_to_Hash160str(k[len(b'feesMap'):])] = ClientResultInterpreter.bytes_to_int(v)
        return fees_dict

    @staticmethod
    def interpret_getPairAttribtutes(Pair):
        pair_attributes = dict()
        for k, v in zip(Pair.keys(), Pair.values()):
            if b'Token' in k:
                pair_attributes[k.split(b'_')[-1].decode()] = ClientResultInterpreter.bytes_to_Hash160str(v)
            else:
                pair_attributes[k.split(b'_')[-1].decode()] = ClientResultInterpreter.bytes_to_int(v)
        return pair_attributes


def sleep_until(timestamp_millisecond: Union[int, float], accuracy = 0.5):
    print(f'sleep until timestamp (millisecond): {timestamp_millisecond}')
    timestamp = timestamp_millisecond / 1000
    while time.time() < timestamp:
        time.sleep(accuracy)


def sleep_for_next_block(sleep_seconds=15):
    print(f'sleep {sleep_seconds} seconds waiting for the next block')
    time.sleep(sleep_seconds)


if __name__ == '__main__':
    print('30 days:', gen_expiry_timestamp_and_str(30))
    print(' 0 days:', gen_expiry_timestamp_and_str(0))
    print('time now:', time.time() * 1000)
    print(' 5 secs:', gen_expiry_timestamp_and_str_in_seconds(5))
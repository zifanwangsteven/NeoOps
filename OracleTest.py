from typing import Any
from boa3.builtin import public
from boa3.builtin.interop import Oracle
from boa3.builtin.interop.contract import call_contract
from boa3.builtin.interop.storage import get, put


STORAGE_KEY = b'STORAGE'

@public
def get_storage()->bytes:
    return get(STORAGE_KEY)

@public
def _deploy():
    return

@public
def oracle_call(url: str):
    Oracle.request(url, '$[-1:]..p', 'store', None, 10000000)

@public
def store(url: str, user_data: Any, code: int, result: bytes):
    put(STORAGE_KEY, result)
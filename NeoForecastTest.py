import os.path
import unittest
import time
from typing import List

from boa3.boa3 import Boa3
from boa3.neo.smart_contract.VoidType import VoidType
from boa3.neo3.vm import VMState
from boa3_test.tests.test_classes.testengine import TestEngine


class TestSmartContract(unittest.TestCase):
    engine: TestEngine

    @classmethod
    def setUpClass(cls):
        print('beginning')
        cls.dirname = '/Users/oujibon/Desktop/NDP'

        test_engine_installation_folder = '/Users/oujibon/neo-devpack-dotnet/src/Neo.TestEngine/Neo.TestEngine.csproj'
        cls.engine = TestEngine(test_engine_installation_folder)

        path = '/Users/oujibon/Desktop/NDP/NeoForecastTest.py'
        cls.nef_path = path.replace('.py', '.nef')

        if not os.path.isfile(cls.nef_path):
            Boa3.compile_and_save(path, output_path=cls.nef_path)
        print('sucess')

    def _pool_init(self, pool_owner: bytes, token_id: int, symbol: str, margin: int, expiry: int, threshold: int, strike: str, description: str):
        self.engine.add_signer_account(pool_owner)
        return self.engine.run(self.nef_path, 'pool_init', pool_owner, token_id, symbol, margin, expiry, threshold, strike, description)

    def test_pool_init(self):
        self.engine.reset_engine()

        pool_owner = bytes(20)
        token_id = 1
        symbol = 'BTCUSDT'
        margin = 100000000
        expiry = int(time.time() * 1000) + 60 * 5 * 1000
        threshold = expiry-1
        strike = '34010.2'
        description = 'Bet for testing'

        result = self._pool_init(pool_owner, token_id, symbol, margin, expiry, threshold, strike, description)
        self.assertEqual(VMState.HALT, self.engine.vm_state)
        self.assertIsInstance(result, bytes)
        self.assertEqual(32, len(result))


if __name__ == 'main':
    unittest.main()
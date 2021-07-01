import os.path
import unittest
from typing import List

from boa3.boa3 import Boa3
from boa3.neo.smart_contract.VoidType import VoidType
from boa3.neo3.vm import VMState
from boa3_test.tests.test_classes.testengine import TestEngine


class TestSmartContract(unittest.TestCase):
    engine: TestEngine

    @classmethod
    def setUpClass(cls):
        folders = os.path.abspath(__file__).split(os.sep)
        cls.dirname = '/'.join(folders[:-2])

        test_engine_installation_folder = '/Users/oujibon/neo-devpack-dotnet/src/Neo.TestEngine'
        cls.engine = TestEngine(test_engine_installation_folder)

        path = f'{cls.dirname}/NeoForecast.py'
        cls.nef_path = path.replace('.py', '.nef')

        if not os.path.isfile(cls.nef_path):
            Boa3.compile_and_save(path, output_path=cls.nef_path)



if __name__ == 'main':
    unittest.main()
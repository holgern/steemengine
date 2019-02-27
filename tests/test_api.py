from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import range
from builtins import super
import unittest
from steemengine.api import Api


class Testcases(unittest.TestCase):
    def test_api(self):
        api = Api()
        result = api.getLatestBlockInfo()
        self.assertTrue(len(result) > 0)
        
        result = api.getBlockInfo(1910)
        self.assertTrue(len(result) > 0)
        
        result = api.getTransactionInfo("e6c7f351b3743d1ed3d66eb9c6f2c102020aaa5d")
        self.assertTrue(len(result) > 0)
        
        result = api.getContract("tokens")
        self.assertTrue(len(result) > 0)
        
        result = api.find("tokens", "tokens")
        self.assertTrue(len(result) > 0)
        
        result = api.findOne("tokens", "tokens")
        self.assertTrue(len(result) > 0)
        
        result = api.get_history("holger80", "NINJA")
        self.assertTrue(len(result) > 0)
     
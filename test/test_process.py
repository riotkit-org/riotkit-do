#!/usr/bin/env python3

from rkd.api.testing import BasicTestingCase
from rkd.process import carefully_decode


class TestProcess(BasicTestingCase):
    def test_carefully_decode(self):
        self.assertEqual(' world', carefully_decode(u'æ'.encode('cp1252') + b' world', 'utf-8'))

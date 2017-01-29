#!/usr/bin/env python
#


import socket
import threading
import unittest

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from selectext import *


class SelectExtTest(unittest.TestCase):

    def createUDPSocket(self, addr, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((addr, port))

        return sock

    def setUp(self):
        self.addr1 = "127.0.0.1"
        self.port1 = 50000
        self.sock1 = self.createUDPSocket(self.addr1, self.port1)

        self.addr2 = "127.0.0.1"
        self.port2 = 50001
        self.sock2 = self.createUDPSocket(self.addr2, self.port2)

    def tearDown(self):
        self.sock1.close()
        self.sock2.close()

    def test_udp_echo(self):

        event = threading.Event()

        selectext = SelectExt()
        selectext.set_reader(self.sock1, event.set)
        selectext.set_reader(self.sock2, \
                lambda: self.sock2.sendto(*self.sock2.recvfrom(2048)))

        def loop():
            while selectext.wait():
                pass

        # Re-use
        for count in range(0,10):
            th = threading.Thread(target=loop, name="select loop")
            th.start()
    
            msg = bytes(b"Hello, world")
            self.sock1.sendto(msg, (self.addr2, self.port2))
            if event.wait():
                recv_msg, peer = self.sock1.recvfrom(2048)
                self.assertEqual(msg, recv_msg)
    
            msg = bytes(b"Good-bye, workd")
            self.sock1.sendto(msg, (self.addr2, self.port2))
            if event.wait():
                event.clear()
                recv_msg, peer = self.sock1.recvfrom(2048)
                self.assertEqual(msg, recv_msg)
    
            self.assertTrue(th.is_alive())
    
            selectext.notify()
    
            th.join()
    
            self.assertFalse(th.is_alive())


########################################################################
# main
########################################################################

if __name__ == '__main__':
    unittest.main(verbosity=2)

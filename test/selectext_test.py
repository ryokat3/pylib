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

    def test_udp_echo(self):

        addr1 = "127.0.0.1"
        port1 = 50000
        sock1 = self.createUDPSocket(addr1, port1)

        addr2 = "127.0.0.1"
        port2 = 50001
        sock2 = self.createUDPSocket(addr2, port2)

        event = threading.Event()

        selectext = SelectExt()
        selectext.set_reader(sock1, event.set)
        selectext.set_reader(sock2, lambda: sock2.sendto(*sock2.recvfrom(2048)))

        def loop():
            while selectext.wait():
                pass

        th = threading.Thread(target=loop, name="select loop")
        th.start()

        msg = "Hello, world"
        sock1.sendto(msg, (addr2, port2))
        if event.wait():
            recv_msg, peer = sock1.recvfrom(2048)
            self.assertEqual(msg, recv_msg)

        msg = "Good-bye, workd"
        sock1.sendto(msg, (addr2, port2))
        if event.wait():
            event.clear()
            recv_msg, peer = sock1.recvfrom(2048)
            self.assertEqual(msg, recv_msg)

        self.assertTrue(th.is_alive())

        selectext.notify()

        th.join()

        self.assertFalse(th.is_alive())

        ## Re-usable test

        th = threading.Thread(target=loop, name="select loop")
        th.start()

        msg = "Hello, world"
        sock1.sendto(msg, (addr2, port2))
        if event.wait():
            recv_msg, peer = sock1.recvfrom(2048)
            self.assertEqual(msg, recv_msg)

        msg = "Good-bye, workd"
        sock1.sendto(msg, (addr2, port2))
        if event.wait():
            event.clear()
            recv_msg, peer = sock1.recvfrom(2048)
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

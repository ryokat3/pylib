#!/usr/bin/env python
#

import errno
import socket
import threading
import time
import unittest

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from selectext import *


class UDPEchoServerTest(unittest.TestCase):

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


class TCPEchoServerTest(unittest.TestCase):

    def createTCPSocket(self, addr, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((addr, port))

        return sock

    def setUp(self):
        self.addr1 = "127.0.0.1"
        self.port1 = 45723
        self.sock1 = self.createTCPSocket(self.addr1, self.port1)

        self.addr2 = "127.0.0.1"
        self.port2 = 0
        self.sock2 = self.createTCPSocket(self.addr2, self.port2)

    def tearDown(self):
        self.sock1.close()
        self.sock2.close()

    def test_tcp_echo(self):

        event = threading.Event()

        selectext = SelectExt()

        def establish():
            conn, peer = self.sock1.accept()
            selectext.set_reader(conn, lambda: conn.send(conn.recv(2048)))

        self.sock1.listen(10)

        selectext.set_reader(self.sock1, establish)
        selectext.set_reader(self.sock2, event.set)
            
        def loop():
            while selectext.wait():
                pass

        th = threading.Thread(target=loop, name="select loop")
        th.start()

        self.sock2.connect((self.addr1, self.port1))

        msg = bytes(b"Hello, world")
        self.sock2.send(msg)
        if event.wait():
            recv_msg = self.sock2.recv(2048)
            self.assertEqual(msg, recv_msg)

        msg = bytes(b"Good-bye, workd")
        self.sock2.send(msg)
        if event.wait():
            event.clear()
            recv_msg = self.sock2.recv(2048)
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

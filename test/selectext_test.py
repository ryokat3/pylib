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
        self.ssock = self.createUDPSocket("127.0.0.1", 0)
        self.csock = self.createUDPSocket("127.0.0.1", 0)

    def tearDown(self):
        self.ssock.close()
        self.csock.close()

    def test_udp_echo(self):

        event = threading.Event()

        selectext = SelectExt()
        selectext.set_reader(self.csock, event.set)
        selectext.set_reader(self.ssock, \
                lambda: self.ssock.sendto(*self.ssock.recvfrom(2048)))

        def loop():
            while selectext.wait():
                pass

        # Re-use
        for count in range(0,10):
            th = threading.Thread(target=loop, name="select loop")
            th.start()
    
            msg = bytes(b"Hello, world")
            self.csock.sendto(msg, self.ssock.getsockname())
            if event.wait():
                event.clear()
                recv_msg, peer = self.csock.recvfrom(2048)
                self.assertEqual(msg, recv_msg)
    
            msg = bytes(b"Good-bye, workd")
            self.csock.sendto(msg, self.ssock.getsockname())
            if event.wait():
                event.clear()
                recv_msg, peer = self.csock.recvfrom(2048)
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
        self.ssock = self.createTCPSocket("127.0.0.1", 0)
        self.csock = self.createTCPSocket("127.0.0.1", 0)

    def tearDown(self):
        self.ssock.close()
        self.csock.close()

    def test_tcp_echo(self):

        event = threading.Event()

        selectext = SelectExt()

        def establish():
            conn, peer = self.ssock.accept()
            selectext.set_reader(conn, lambda: conn.send(conn.recv(2048)))

        self.ssock.listen(10)

        selectext.set_reader(self.ssock, establish)
        selectext.set_reader(self.csock, event.set)
            
        self.csock.connect(self.ssock.getsockname())

        def loop():
            while selectext.wait():
                pass

        for count in range(0,6):
            th = threading.Thread(target=loop, name="select loop")
            th.start()
    
            msg = bytes(b"Hello, world")
            self.csock.send(msg)
            if event.wait():
                event.clear()
                recv_msg = self.csock.recv(2048)
                self.assertEqual(msg, recv_msg)
    
            msg = bytes(b"Good-bye, workd")
            self.csock.send(msg)
            if event.wait():
                event.clear()
                recv_msg = self.csock.recv(2048)
                self.assertEqual(msg, recv_msg)
    
            self.assertTrue(th.is_alive())
    
            selectext.notify()
    
            th.join()
    
            self.assertFalse(th.is_alive())


class TimeoutTest(unittest.TestCase):

    def createUDPSocket(self, addr, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((addr, port))

        return sock

    def setUp(self):
        self.ssock = self.createUDPSocket("127.0.0.1", 0)
        self.csock = self.createUDPSocket("127.0.0.1", 0)

    def tearDown(self):
        self.ssock.close()
        self.csock.close()


    def test_timeout(self):

        event = threading.Event()

        # Server only receive
        #
        selectext = SelectExt()

        now1 = time.time()
        idx = selectext.set_timeout_handler(0.5, event.set)
        selectext.set_reader(self.ssock, \
                lambda: self.ssock.recvfrom(2048))

        def loop():
            while selectext.wait():
                pass

        th = threading.Thread(target=loop, name="select loop")
        th.start()

        msg = bytes(b"Hello, world")

        self.csock.sendto(msg, self.ssock.getsockname())
        if event.wait():
            event.clear()
            elapse = time.time() - now1
            self.assertTrue(0.45 < elapse and elapse < 0.55)

        selectext.notify()
        th.join()


########################################################################
# main
########################################################################

if __name__ == '__main__':
    unittest.main(verbosity=2)

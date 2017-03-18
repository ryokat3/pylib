#!/usr/bin/env python
#

#
# The MIT License (MIT)
# 
# Copyright (c) 2017 wak109
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

import select
import socket
import sys
import time
import threading


try:
    from socket import socketpair
except ImportError:
    import errno

    #
    # Copied From:
    #   https://gist.github.com/geertj/4325783
    #
    def socketpair(
            sock_family=socket.AF_INET,
            sock_type=socket.SOCK_STREAM,
            sock_proto=0):
        """Emulate the Unix socketpair() function on Windows."""

        # We create a connected TCP socket.
        # Note the trick with setblocking(0)
        # that prevents us from having to create a thread.

        lsock = socket.socket(sock_family, sock_type, sock_proto)
        lsock.bind(('localhost', 0)) 
        lsock.listen(1)
        addr, port = lsock.getsockname()
        csock = socket.socket(sock_family, sock_type, sock_proto)
        csock.setblocking(0)
        try:
            csock.connect((addr, port))
        except socket.error as e:
            if e.errno != errno.WSAEWOULDBLOCK:
                raise
        ssock, addr = lsock.accept()
        csock.setblocking(1)
        lsock.close()
        return (ssock, csock)


class SelectExt(object):

    def __init__(self):
        self.readers = {}
        self.writers = {}
        self.timers = {}
        self.error_handlers = {}

        self.rlock = threading.RLock()
        self.notify_lock = threading.Lock()
        self.pair = socketpair()
        self.cont = True

    def __del__(self):
        self.pair[0].shutdown(socket.SHUT_RDWR)
        self.pair[1].shutdown(socket.SHUT_RDWR)
        self.pair[0].close()
        self.pair[1].close()

    def set_reader(self, sock, callback):
        with self.rlock:
            self.readers[sock] = callback

    def set_writer(self, sock, callback):
        with self.rlock:
            self.writers[sock] = callback

    def set_timer(self, timeout, callback):
        with self.rlock:
            idx = object()
            self.timers[idx] = (time.time() + timeout, callback)

            self.cont = True
            self.pair[1].send(bytes(b'@'))

            return idx

    def set_error_handler(self, sock, callback):
        with self.rlock:
            self.error_handlers[sock] = callback

    def unset_reader(self, sock):
        with self.rlock:
            if sock in self.readers:
                del self.readers[sock]

    def unset_writer(self, sock):
        with self.rlock:
            if sock in self.writers:
                del self.writers[sock]

    def unset_timer(self, idx):
        with self.rlock:
            if idx in self.timers:
                del self.timers[idx]

            self.cont = True
            self.pair[1].send(bytes(b'@'))

    def unset_error_handler(self, sock):
        with self.rlock:
            if sock in self.error_handlers:
                del self.error_handlers[sock]

    def notify(self):
        with self.notify_lock:
            self.cont = False
            self.pair[1].send(bytes(b'@'))
          
    def wait(self):

        with self.rlock:

            if self.timers:

                now = time.time()
                timeout = max(min([ expire for expire, callback in \
                    self.timers.values() ] + [now]) - now, 0)

                ready_to_read, ready_to_write, in_error = select.select(
                    list(self.readers.keys()) + [ self.pair[0], ],
                    self.writers.keys(),
                    self.error_handlers.keys(),
                    timeout)
            else:
                ready_to_read, ready_to_write, in_error = select.select(
                    list(self.readers.keys()) + [ self.pair[0], ],
                    self.writers.keys(),
                    self.error_handlers.keys())
    
            for sock in ready_to_read:
                if sock != self.pair[0]:
                    self.readers[sock]()
            for sock in ready_to_write:
                self.writers[sock]()
            for sock in in_error:
                self.error_handlers[sock]()

            now = time.time()
            for idx in [ idx for idx in self.timers.keys() \
                    if now > self.timers[idx][0] ]:
                self.timers[idx][1]()
                del self.timers[idx]

            if self.pair[0] in ready_to_read:
                # TODO: any better way to clear the socket completely ?
                self.pair[0].recv(4096)
                return self.cont
            else:
                return True

########################################################################
# main
########################################################################

if __name__ == '__main__':
    import unittest
    from test.selectext_test import *

    unittest.main(verbosity=2)

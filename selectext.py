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
import threading


class SelectExt(object):

    def __init__(self):
        self.readers = {}
        self.writers = {}
        self.error_handlers = {}

        self.rlock = threading.RLock()
        self.notify_lock = threading.Lock()
        self.pair = socket.socketpair()

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

    def set_error_handler(self, sock, callback):
        with self.rlock:
            self.error_handlers[sock] = callback

    def unset_reader(self, sock):
        with self.rlock:
            del self.readers[sock]

    def unset_writer(self, sock):
        with self.rlock:
            del self.writers[sock]

    def unset_error_handler(self, sock):
        with self.rlock:
            del self.error_handlers[sock]

    def notify(self):
        with self.notify_lock:
            self.pair[1].send('@')
          
    def wait(self, timeout=0):

        with self.rlock:
            ready_to_read, ready_to_write, in_error = select.select(
                    self.readers.keys() + [ self.pair[0], ],
                    self.writers.keys(),
                    self.error_handlers.keys(),
                    timeout)
    
            for sock in ready_to_read:
                if sock != self.pair[0]:
                    self.readers[sock]()
            for sock in ready_to_write:
                self.writers[sock]()
            for sock in in_error:
                self.error_handlers[sock]()

            if self.pair[0] in ready_to_read:
                # TODO: any better way to clear the socket completely ?
                self.pair[0].recv(4096)
                return False
            else:
                return True

########################################################################
# main
########################################################################

if __name__ == '__main__':
    import unittest
    from test.selectext_test import *

    unittest.main(verbosity=2)

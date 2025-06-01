# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

import select
import socket
from typing import List

from dawscript_core import host
from dawscript_core.util import add_site_packages

add_site_packages(__file__)

import rpyc
from rpyc.core.protocol import Connection


rpyc_socket: socket.socket
connections: List[Connection] = []


def on_script_start():
    global rpyc_socket
    rpyc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    rpyc_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    rpyc_socket.bind(('localhost', 18861))
    rpyc_socket.listen(5)
    rpyc_socket.setblocking(False)
    host.display(f"Bound to {rpyc_socket.getsockname()}")


def on_script_stop():
    try:
        for conn in connections:
            try:
                conn.close()
            except Exception as e:
                host.log(e)
        rpyc_socket.close()
    except Exception as e:
        host.log(e)


def host_callback(midi: List[bytes]):
    readable, _, _ = select.select([rpyc_socket] + connections, [], [], 0)
    for sock in readable:
        if sock is rpyc_socket:
            conn, addr = sock.accept()
            connections.append(rpyc.classic.connect_stream(rpyc.SocketStream(conn)))
            host.display(f"Connected: {addr}")
        else:
            for conn in connections:
                try:
                    conn.serve()
                except Exception as e:
                    host.log(e)
                    conn.close()
                    connections.remove(conn)
                    break

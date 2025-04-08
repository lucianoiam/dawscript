# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

import asyncio
import json
import math
import os
import re
import socket
import time
from typing import Any, Callable, Dict, List

import websockets
from aiohttp import web, web_runner

import host
from util import dawscript_path

from . import dnssd
from .protocol import replace_inf, ReprJSONDecoder, ReprJSONEncoder

BUILTIN_HTDOCS_PATH = os.path.join("extra", "web")
LOG_TAG = "server.py"

_htdocs_path: str = None
_loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
_cleanup: List[Callable] = []
_listener_del: Dict[str, Dict[int, Callable]] = {}
_setter_call_src: Dict[str, str] = {}
_setter_call_t: float = 0


def start(htdocs_path, ws_port=49152, http_port=8080, service_name=None) -> List[str]:
    global _htdocs_path
    _htdocs_path = htdocs_path

    addrs = ["127.0.0.1"]
    lan_addr = None

    try:
        lan_addr = _get_bind_address()
        addrs.append(socket.inet_ntoa(lan_addr))
    except:
        pass

    try:
        ws = _loop.run_until_complete(_ws_serve(addrs, ws_port))
        if len(ws) > 0:
            _cleanup.append(ws[0].close)
        else:
            raise Exception('could not create websocket')
        if len(ws) > 1:
            _cleanup.append(ws[1].close)
    except Exception as e:
        host.log(f"{LOG_TAG} _ws_serve(): {e}")
        return []

    try:
        http = _loop.run_until_complete(_http_serve(addrs, http_port))
        _cleanup.append(lambda: _loop.create_task(http.cleanup()))
    except Exception as e:
        host.log(f"{LOG_TAG} _http_serve(): {e}")
        stop()
        return []

    if lan_addr is not None and service_name is not None:
        try:
            dnssd.register_service(service_name, "_http._tcp", http_port, lan_addr)
            _cleanup.append(dnssd.unregister_service)
        except Exception as e:
            host.log(f"{LOG_TAG} register_service(): {e}")

    qs = f"?port={ws_port}" if ws_port != 49152 else ""
    urls = [f"http://{addr}:{http_port}{qs}" for addr in addrs]

    return urls


def stop():
    for func in _cleanup:
        func()


def tick():
    _unmute_remote_listeners()
    _loop.run_until_complete(_noop())


async def _noop():
    pass


async def _ws_serve(addrs, port) -> List[asyncio.AbstractServer]:
    return [await websockets.serve(_ws_handle, addr, port) for addr in addrs]


async def _ws_handle(ws, path):
    client = str(ws.id)

    async for message in ws:
        (seq, func_name, *args) = json.loads(message, cls=ReprJSONDecoder)

        m = re.match(r"^(add|del)_([a-z_]+)_listener$", func_name)

        if m:
            action, prop = m.groups()

            if action == "add":
                await _add_listener(ws, seq, client, args[0], prop)
                await _send_ack(ws, seq)
            elif action == "del":
                await _del_listener(ws, seq, client, args[0])
                await _send_ack(ws, seq)

            continue

        try:
            result = getattr(host, func_name)(*args)
        except Exception as e:
            result = f"error:{e}"
            host.log(e)

        m = re.match(r"^set_([a-z_]+)$", func_name)

        if m:
            _mute_remote_listener(client, args[0], m.groups()[0])
            # skip ack
            continue

        await _send_message(ws, seq, result)

    _cleanup_client(client)


async def _http_serve(addrs, port) -> web_runner.AppRunner:
    app = web.Application()
    app.router.add_get("/{filename:.*}", _http_handle)

    runner = web.AppRunner(app)
    await runner.setup()

    for addr in addrs:
        site = web.TCPSite(runner, addr, port)
        await site.start()

    return runner


async def _http_handle(request):
    filename = request.match_info.get("filename")

    if filename.startswith(BUILTIN_HTDOCS_PATH):
        filepath = dawscript_path(filename)
    else:
        filepath = os.path.join(_htdocs_path, filename)

    if os.path.isdir(filepath):
        filepath = os.path.join(filepath, "index.html")

    if not os.path.exists(filepath):
        return web.Response(status=404, text="File Not Found")

    return web.FileResponse(filepath)


async def _send_message(ws, seq, payload):
    message = [seq]

    if payload is not None:
        message.append(replace_inf(payload))

    await ws.send(json.dumps(message, cls=ReprJSONEncoder))


async def _send_ack(ws, seq):
    await _send_message(ws, seq, None)


async def _add_listener(ws, seq, client, target, prop):
    def listener(v, c_ws=ws, c_seq=seq, c_tp=f"{target}_{prop}"):
        return _call_remote_listener(c_ws, c_seq, c_tp, v)

    setter = getattr(host, f"add_{prop}_listener")
    setter(target, listener)

    deleter = getattr(host, f"del_{prop}_listener")
    bound_deleter = lambda d=deleter, t=target, l=listener: d(t, l)

    if client not in _listener_del:
        _listener_del[client] = {}

    _listener_del[client][seq] = bound_deleter


async def _del_listener(ws, seq, client, listener_seq):
    if (
        client not in _listener_del
        or listener_seq not in _listener_del[client]
    ):
        raise Exception("Listener not registered")

    bound_deleter = _listener_del[client][listener_seq]
    bound_deleter()

    del _listener_del[client][listener_seq]

    if not _listener_del[client]:
        del _listener_del[client]


def _mute_remote_listener(client, target, prop):
    global _setter_call_t
    _setter_call_t = time.time()
    _setter_call_src[f"{target}_{prop}"] = client


def _unmute_remote_listeners():
    global _setter_call_src, _setter_call_t

    if _setter_call_t > 0 and (time.time() - _setter_call_t) > 0.01:
        _setter_call_src = {}
        _setter_call_t = 0


def _call_remote_listener(ws, seq, key_tp, value):
    client = str(ws.id)

    try:
        if _setter_call_src.get(key_tp) != client:
            _loop.run_until_complete(_send_message(ws, seq, value))
    except Exception as e:
        host.log(e)
        _cleanup_client(client)


def _cleanup_client(client):
    if client not in _listener_del:
        return

    for deleter in _listener_del[client].values():
        deleter()

    del _listener_del[client]


def _get_bind_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    naddr = socket.inet_aton(s.getsockname()[0])
    s.close()

    return naddr

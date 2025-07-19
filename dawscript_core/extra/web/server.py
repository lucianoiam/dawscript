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

from dawscript_core import host
from dawscript_core.util import dawscript_path

from . import dnssd
from .protocol import replace_inf, JSONDecoder, JSONEncoder

BUILTIN_HTDOCS_PATH = os.path.join("dawscript_core", "extra", "web")
LOG_TAG = "server.py"
LISTENER_MUTE_MS = 100

_loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
_htdocs_path: str = None
_cleanup: List[Callable] = []
_listener_remover: Dict[str, Dict[int, Callable]] = {}
_setter_call_src: Dict[str, str] = {}
_setter_call_t: float = 0

JSONEncoder.get_object_id = host.get_object_id


def start(htdocs_path, ws_port=49152, http_port=8080, service_name=None) -> List[str]:
    global _htdocs_path
    _htdocs_path = htdocs_path

    addrs = ["127.0.0.1"]
    lan_addr = None

    try:
        lan_addr = _get_bind_address()
        addrs.append(lan_addr)
    except:
        pass

    try:
        _loop.run_until_complete(_ws_serve(addrs, ws_port))
        _loop.run_until_complete(_http_serve(addrs, http_port))

        if lan_addr is not None and service_name is not None:
            dnssd.register_service(service_name, "_http._tcp", http_port, lan_addr)
            _cleanup.append(dnssd.unregister_service)
    except Exception as e:
        stop()
        raise e

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
    servers = []

    for addr in addrs:
        try:
            server = await websockets.serve(_ws_handle, addr, port)
            _cleanup.append(server.close)
            servers.append(server)
        except Exception as e:
            host.log(f"{LOG_TAG} _ws_serve(): {e}")

    if not servers:
        raise Exception('Could not start websocket server')


async def _ws_handle(ws, path):
    client = str(ws.id)

    async for message in ws:
        (seq, func_name, *args) = json.loads(message, cls=JSONDecoder)

        m = re.match(r"^(add|remove)_([a-z_]+)_listener$", func_name)

        if m:
            action, prop = m.groups()

            if action == "add":
                await _add_listener(ws, seq, client, args[0], prop)
                await _send_ack(ws, seq)
            elif action == "remove":
                await _remove_listener(ws, seq, client, args[0])
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


async def _http_serve(addrs, port):
    app = web.Application(middlewares=[inject_dawscript_tag])
    app.router.add_get("/{filename:.*}", _http_handle)

    runner = web.AppRunner(app)
    await runner.setup()
    _cleanup.append(lambda: _loop.create_task(runner.cleanup()))

    for addr in addrs:
        site = web.TCPSite(runner, addr, port)
        await site.start()


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

    await ws.send(json.dumps(message, cls=JSONEncoder))


async def _send_ack(ws, seq):
    await _send_message(ws, seq, None)


async def _add_listener(ws, seq, client, target, prop):
    def listener(v, c_ws=ws, c_seq=seq, c_tp=f"{target}_{prop}"):
        return _call_remote_listener(c_ws, c_seq, c_tp, v)

    setter = getattr(host, f"add_{prop}_listener")
    setter(target, listener)

    remover = getattr(host, f"remove_{prop}_listener")
    bound_remover = lambda r=remover, t=target, l=listener: r(t, l)

    if client not in _listener_remover:
        _listener_remover[client] = {}

    _listener_remover[client][seq] = bound_remover


async def _remove_listener(ws, seq, client, listener_seq):
    if (
        client not in _listener_remover
        or listener_seq not in _listener_remover[client]
    ):
        #raise Exception("Listener not registered")
        host.log(f"{LOG_TAG} listener not registered - {listener_seq}")
        return

    bound_remover = _listener_remover[client][listener_seq]
    bound_remover()

    del _listener_remover[client][listener_seq]

    if not _listener_remover[client]:
        del _listener_remover[client]


def _mute_remote_listener(client, target, prop):
    global _setter_call_t
    _setter_call_t = time.time()
    _setter_call_src[f"{target}_{prop}"] = client


def _unmute_remote_listeners():
    global _setter_call_src, _setter_call_t

    if _setter_call_t > 0 and (time.time() - _setter_call_t) > 0.001*LISTENER_MUTE_MS:
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
    if client not in _listener_remover:
        return

    for remover in _listener_remover[client].values():
        remover()

    del _listener_remover[client]


def _get_bind_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    naddr = socket.inet_aton(s.getsockname()[0])
    s.close()

    return socket.inet_ntoa(naddr)

@web.middleware
async def inject_dawscript_tag(request, handler):
    response = await handler(request)
    
    if isinstance(response, web.FileResponse):
        file_path = str(response._path)
        
        if file_path.endswith(".html"):
            with open(file_path, 'r') as file:
                content = file.read()

            script_tag = f'<script src="/{BUILTIN_HTDOCS_PATH}/dawscript.js"></script>'
            pattern = re.compile(r'(<body[^>]*>)', re.IGNORECASE)
            content = pattern.sub(r'\1\n' + script_tag, content, count=1)

            return web.Response(text=content, content_type='text/html')

    return response

# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

import asyncio
import json
import math
import os
import re
import socket
from typing import Any, Callable, Dict, List

import websockets
from aiohttp import web, web_runner

import host
from util import dawscript_path

from . import dnssd
from .protocol import replace_inf, ReprJSONDecoder, ReprJSONEncoder

BUILTIN_HTDOCS_PATH = os.path.join('extra', 'web')

_loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
_setter_src: Dict[str,str] = {}
_setter_n: int = 0
_cleanup: List[Callable] = []
_htdocs_path: str = None

def start(htdocs_path, ws_port=49152, http_port=8080,
          service_name=None) -> List[str]:
   global _htdocs_path
   _htdocs_path = htdocs_path

   lan_addr = _get_bind_address()
   lan_addr_str = socket.inet_ntoa(lan_addr)
   addrs = ['127.0.0.1', lan_addr_str]

   ws = _loop.run_until_complete(_ws_serve(addrs, ws_port))
   http = _loop.run_until_complete(_http_serve(addrs, http_port))

   if service_name is not None:
      try:
         dnssd.register_service(service_name, '_http._tcp', http_port, lan_addr)
         _cleanup.append(dnssd.unregister_service)
      except Exception as e:
         host.display(f'dawscript: {e}')

      _cleanup.append(lambda: _loop.create_task(http.cleanup()))
      _cleanup.append(ws[1].close)
      _cleanup.append(ws[0].close)

   qs = f'?port={ws_port}' if ws_port != 49152 else ''
   urls = [f'http://{addr}:{http_port}{qs}' for addr in addrs]

   return urls

def stop():
   for func in _cleanup:
      func()

def tick():
   _unlock_remote_listeners()
   _loop.run_until_complete(_noop())

async def _noop():
   pass

async def _ws_serve(addrs, port) -> List[asyncio.AbstractServer]:
   return [await websockets.serve(_ws_handle, addr, port) for addr in addrs]

async def _ws_handle(ws, path):
   client = str(ws.id)

   async for message in ws:
      (seq, func_name, *args) = json.loads(message, cls=ReprJSONDecoder)
      func = getattr(host, func_name)
      m = re.match(r"^(add|del)_([a-z_]+)_listener$", func_name)
      if m:
         g = m.groups()
         if g[0] == 'add':
            target = f'{args[0]}_{g[1]}'
            listener = lambda v, c_ws=ws, c_seq=seq, c_target=target: _call_remote_listener(c_ws, c_seq, c_target, v)
            args.append(listener)
         elif g[0] == 'del':
            # TODO - remove
            pass
      try:
         result = func(*args)
         m = re.match(r"^set_([a-z_]+)$", func_name)
         if m:
            target = f'{args[0]}_{m.groups()[0]}'
            _setter_src[target] = client
            global _setter_n
            _setter_n = 2
      except Exception as e:
         result = f'error:{e}'
      if result is not None:
         await _send_message(ws, seq, result)
   # TODO - remove registered listeners for client

async def _http_serve(addrs, port) -> web_runner.AppRunner:
   app = web.Application()
   app.router.add_get('/{filename:.*}', _http_handle)

   runner = web.AppRunner(app)
   await runner.setup()

   for addr in addrs:
      site = web.TCPSite(runner, addr, port)
      await site.start()

   return runner

async def _http_handle(request):
   filename = request.match_info.get('filename')

   if filename.startswith(BUILTIN_HTDOCS_PATH):
      filepath = dawscript_path(filename)
   else:
      filepath = os.path.join(_htdocs_path, filename)

   if os.path.isdir(filepath):
      filepath = os.path.join(filepath, 'index.html')

   if not os.path.exists(filepath):
      return web.Response(status=404, text='File Not Found')

   return web.FileResponse(filepath)

async def _send_message(ws, seq, data):
   message = json.dumps([seq, replace_inf(data)], cls=ReprJSONEncoder)
   await ws.send(message)

def _call_remote_listener(ws, seq, target, value):
   try:
      client = str(ws.id)
      if _setter_src.get(target) != client:
         _loop.run_until_complete(_send_message(ws, seq, value))
   except Exception as e:
      host.log(e)
      # TODO - remove registered listeners for client

def _unlock_remote_listeners():
   global _setter_src, _setter_n
   if _setter_n == 0:
      return
   _setter_n -= 1
   if _setter_n == 0:
      _setter_src = {}

def _get_bind_address():
   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   s.connect(('8.8.8.8', 80))
   naddr = socket.inet_aton(s.getsockname()[0])
   s.close()
   return naddr

# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

import asyncio
import json
import os
import re
import sys

import websockets
from aiohttp import web, web_runner

import host
from util import dawscript_path

from .protocol import replace_inf, ReprJSONDecoder, ReprJSONEncoder

PORT_WEBSOCKET = 49152
PORT_HTTP = 8080

loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
ws_server: asyncio.AbstractServer = None
http_server: web_runner.AppRunner = None

def start():
   global ws_server
   ws_server = loop.run_until_complete(_ws_serve())
   global http_server
   http_server = loop.run_until_complete(_http_serve())

def stop():
   loop.run_until_complete(http_server.cleanup())
   ws_server.close()

def do_work():
   loop.run_until_complete(_noop())

async def _noop():
   pass

async def _ws_serve():
   return await websockets.serve(_ws_handle, 'localhost', PORT_WEBSOCKET)

async def _ws_handle(ws, path):
   async for message in ws:
      (seq, func_name, *args) = json.loads(message, cls=ReprJSONDecoder)
      func = getattr(host, func_name)
      if re.match(r'^set_[a-z_]+_listener$', func_name):
         func(args[0], lambda result: _call_listener(ws, seq, result))
         result = None
      else:
         try:
            result = func(*args)
         except Exception as e:
            result = f'error:{e}'
      await _send_message(ws, seq, result)

async def _http_serve():
   app = web.Application()
   app.router.add_get('/{filename:.*}', _http_handle)

   runner = web.AppRunner(app)
   await runner.setup()

   site = web.TCPSite(runner, '127.0.0.1', PORT_HTTP)
   await site.start()

   return runner

async def _http_handle(request):
   htdocs = dawscript_path('examples', 'browser_js', 'htdocs')
   filepath = os.path.join(htdocs, request.match_info.get('filename'))

   if os.path.isdir(filepath):
      filepath = os.path.join(filepath, 'index.html')

   if not os.path.exists(filepath):
      return web.Response(status=404, text='File Not Found')

   return web.FileResponse(filepath)

async def _send_message(ws, seq, data):
   message = json.dumps([seq, replace_inf(data)], cls=ReprJSONEncoder)
   await ws.send(message)

def _call_listener(ws, seq, data):
   loop.run_until_complete(_send_message(ws, seq, data))

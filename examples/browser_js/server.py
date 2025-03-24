# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

import asyncio
import json
import os
import sys

import websockets
from aiohttp import web

import host
from util import dawscript_path

from .protocol import replace_inf, ReprJSONDecoder, ReprJSONEncoder

PORT_WEBSOCKET = 49152
PORT_HTTP = 8080

loop = asyncio.get_event_loop()

def start():
   loop.run_until_complete(_ws_serve())
   loop.run_until_complete(_http_serve())

def do_work():
   loop.run_until_complete(_noop())

async def _ws_serve():
   return await websockets.serve(_ws_handle, 'localhost', PORT_WEBSOCKET)

async def _ws_handle(ws, path):
   async for message in ws:
      (seq, func, *args) = json.loads(message, cls=ReprJSONDecoder)
      try:
         result = getattr(host, func)(*args)
      except Exception as e:
         result = f'error:{e}'
      message = json.dumps([seq, replace_inf(result)], cls=ReprJSONEncoder)
      await ws.send(message)

async def _http_serve():
   app = web.Application()
   app.router.add_get('/{filename:.*}', _http_handle)

   runner = web.AppRunner(app)
   await runner.setup()

   site = web.TCPSite(runner, '127.0.0.1', PORT_HTTP)
   await site.start()

async def _http_handle(request):
   htdocs = dawscript_path('examples', 'browser_js', 'htdocs')
   filepath = os.path.join(htdocs, request.match_info.get('filename'))

   if os.path.isdir(filepath):
      filepath = os.path.join(filepath, 'index.html')

   if not os.path.exists(filepath):
      return web.Response(status=404, text='File Not Found')

   return web.FileResponse(filepath)

async def _noop():
   pass

# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

import asyncio
import os
import sys

import websockets
from aiohttp import web

from host import log
from util import dawscript_path

loop = asyncio.get_event_loop()

def start():
    loop.run_until_complete(_ws_serve())
    loop.run_until_complete(_http_serve())

def do_work():
    loop.run_until_complete(_noop())

async def _ws_serve():
    return await websockets.serve(_ws_handle, 'localhost', 8765)

async def _ws_handle(websocket, path):
    async for message in websocket:
        log(message.strip())
        await websocket.send('ACK')

async def _http_serve():
    app = web.Application()
    app.router.add_get('/{filename:.*}', _http_handle)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, '127.0.0.1', 8080)
    await site.start()

async def _http_handle(request):
    htdocs = dawscript_path('examples', 'browser_js')
    filepath = os.path.join(htdocs, request.match_info.get('filename'))

    if os.path.isdir(filepath):
        filepath = os.path.join(filepath, 'index.html')

    if not os.path.exists(filepath):
        return web.Response(status=404, text='File Not Found')

    return web.FileResponse(filepath)

async def _noop():
    pass

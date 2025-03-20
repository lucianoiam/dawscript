# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

import asyncio
import os
import sys
from typing import List

from host import ALL_MIDI_INPUTS, Config, log
from util import add_site_packages, dawscript_path

ds_path = dawscript_path('examples', 'browser_js')
add_site_packages(ds_path)

import websockets
from aiohttp import web

loop = asyncio.get_event_loop()

def host_callback(midi: List[bytes]):
    loop.run_until_complete(_noop())

async def _noop():
    pass

""" WebSockets server """
async def _ws_handle(websocket, path):
    async for message in websocket:
        log(message.strip())
        await websocket.send('ACK')

async def _ws_serve():
    return await websockets.serve(_ws_handle, 'localhost', 8765)

ws_server = loop.run_until_complete(_ws_serve())

""" HTTP server """
try:
    async def _http_handle(request):
        filepath = os.path.join(ds_path, request.match_info.get('filename'))

        if os.path.isdir(filepath):
            filepath = os.path.join(filepath, 'index.html')

        if not os.path.exists(filepath):
            return web.Response(status=404, text='File Not Found')

        return web.FileResponse(filepath)

    async def _http_serve():
        app = web.Application()
        app.router.add_get('/{filename:.*}', _http_handle)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '127.0.0.1', 8080)
        await site.start()

    loop.run_until_complete(_http_serve())
except Exception as e:
    log(e)

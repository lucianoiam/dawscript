# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

import asyncio

from host import ALL_MIDI_INPUTS, Config, log
from thirdparty import websockets

# TODO

config = Config(midi_inputs=ALL_MIDI_INPUTS)
loop = asyncio.get_event_loop()

def host_callback(midi: list[bytes]):
    loop.run_until_complete(_noop())

async def _noop():
    pass

async def _ws_handler(websocket, path):
    async for message in websocket:
        log(message.strip())
        await websocket.send('ACK')

async def _ws_serve():
    return await websockets.serve(_ws_handler, 'localhost', 8765)

server = loop.run_until_complete(_ws_serve())

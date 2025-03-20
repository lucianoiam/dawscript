# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

import jack
import queue
import os
import signal
import sys
import time
import threading
from typing import Any, Callable, List

from .shared import load_controller
from .types import ParameterHandle, PluginHandle, TrackHandle

_controller = None
_jack_client: jack.Client = None
_jack_midi_in: jack.OwnPort = None
_midi_queue = queue.Queue()

def name() -> str:
   return 'cli'

def log(message: str):
   print(message)

def set_context(context: Any):
   pass

def run_loop():
   global _controller, _jack_client, _jack_midi_in

   _controller = load_controller()
   ev_port_reg = threading.Event()
   ev_quit = threading.Event()

   try:
      _jack_client = jack.Client(f'dawscript_{os.urandom(2).hex()}',
         no_start_server=True)
   except jack.JackOpenError:
      sys.exit(1)

   _jack_midi_in = _jack_client.midi_inports.register(f'input')
   _jack_client.set_process_callback(_jack_proc)
   _jack_client.set_port_registration_callback(lambda p,r: ev_port_reg.set())
   _jack_client.activate()

   signal.signal(signal.SIGINT, lambda sig, frame: ev_quit.set())

   while not ev_quit.is_set():
      if ev_port_reg.is_set():
         ev_port_reg.clear()
         _connect_ports()
      _controller.host_callback(_read_midi_events())
      time.sleep(1/30)

   _jack_client.deactivate()
   _jack_client.close()

def get_tracks() -> List[TrackHandle]:
   log(f'stub: get_tracks()')
   return []

def get_track(name: str) -> TrackHandle:
   log(f'stub: get_track( {name} )')
   return name

def is_track_mute(track: TrackHandle) -> bool:
   log(f'stub: is_track_mute( {track} )')
   return False

def set_track_mute(track: TrackHandle, mute: bool):
   log(f'stub: set_track_mute( {track} )')

def set_track_mute_listener(track: TrackHandle, listener: Callable[[bool],None]):
   log(f'stub: set_track_mute_listener( {track}, {listener} )')

def get_track_volume(track: TrackHandle) -> float:
   log(f'stub: get_track_volume( {track} )')
   return 0.0

def set_track_volume(track: TrackHandle, volume_db: float):
   log(f'stub: set_track_volume( {track}, {volume_db} )')

def set_track_volume_listener(track: TrackHandle, listener: Callable[[float],None]):
   log(f'stub: set_track_volume_listener( {track}, {listener} )')

def get_track_pan(track: TrackHandle) -> float:
   log(f'stub: get_track_pan( {track} )')
   return 0.0

def set_track_pan_listener(track: TrackHandle, listener: Callable[[float],None]):
   log(f'stub: set_track_pan_listener( {track}, {listener} )')

def set_track_pan(track: TrackHandle, pan: float):
   log(f'stub: set_track_pan( {track}, {pan} )')

def get_plugin(track: TrackHandle, name: str) -> PluginHandle:
   log(f'stub: get_plugin( {track}, {name} )')
   return name

def is_plugin_enabled(plugin: PluginHandle) -> bool:
   log(f'stub: is_plugin_enabled( {plugin} )')
   return False

def set_plugin_enabled(plugin: PluginHandle, enabled: bool):
   log(f'stub: set_plugin_enabled( {plugin}, {enabled} )')

def set_plugin_enabled_listener(plugin: PluginHandle, listener: Callable[[bool],None]):
   log(f'stub: set_plugin_enabled_listener( {plugin}, {listener} )')

def get_parameter(plugin: PluginHandle, name: str) -> ParameterHandle:
   log(f'stub: get_parameter( {plugin}, {name} )')
   return name

def get_parameter_range(param: ParameterHandle) -> (float, float):
   log(f'stub: get_parameter_range( {param} )')
   return (0, 1.0)

def get_parameter_value(param: ParameterHandle) -> float:
   log(f'stub: get_parameter_value( {param} )')
   return 0.0

def set_parameter_value(param: ParameterHandle, value: float):
   log(f'stub: set_parameter_value( {param}, {value} )')

def set_parameter_value_listener(param: ParameterHandle, listener: Callable[[float],None]):
   log(f'stub: set_parameter_value_listener( {param}, {listener} )')

def _jack_proc(frames: int):
   for offset, data in _jack_midi_in.incoming_midi_events():
      _midi_queue.put_nowait(bytes(data))

def _connect_ports():
   try:
      midi_inputs = _jack_client.get_ports(
         name_pattern='|'.join(_controller.config.midi_inputs),
         is_midi=True, is_output=True)
   except AttributeError:
      print('config not available', file=sys.stderr)
      return
   for some_midi_input in midi_inputs:
      try:
         if not _jack_midi_in.is_connected_to(some_midi_input):
            _jack_midi_in.connect(some_midi_input)
            log(f'{some_midi_input.name} <- {_jack_midi_in.name}')
      except jack.JackError as e:
         print(str(e), file=sys.stderr)

def _read_midi_events():
   events = list()
   while _midi_queue.qsize() > 0:
      events.append(_midi_queue.get_nowait())
   return events

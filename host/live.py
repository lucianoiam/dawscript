# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

from .types import IncompatibleEnvironmentError

try:
   import Live
   from _Framework.ControlSurface import ControlSurface
except ModuleNotFoundError:
   raise IncompatibleEnvironmentError

import importlib
import math
import sys
from typing import Any

from .shared import load_controller
from .types import (ParameterHandle, ParameterNotFoundError, PluginHandle,
   PluginNotFoundError, TrackHandle, TrackNotFoundError)

_control_surface = None

def name() -> str:
   return 'live'

# tail -f ~/Library/Preferences/Ableton/Live\ x.x.x/Log.txt
def log(message: str):
   if _control_surface is not None:
      _control_surface.log_message(message)
   else:
      print(message, file=sys.stderr)

def set_context(context: Any):
   global _control_surface
   _control_surface = context['control_surface']

def run_loop():
   pass

def get_track(name: str) -> TrackHandle:
   name_lower = name.lower()
   for track in _get_document().tracks:
      if track.name.lower() == name_lower:
         return track
   raise TrackNotFoundError(name)

def is_track_mute(track: TrackHandle) -> bool:
   return track.mute

def set_track_mute(track: TrackHandle, mute: bool):
   track.mute = mute

def get_track_volume(track: TrackHandle) -> float:
   return _vol_value_to_db(track.mixer_device.volume.value)

def set_track_volume(track: TrackHandle, volume_db: float):
   track.mixer_device.volume.value = _db_to_vol_value(volume_db)

def get_track_pan(track: TrackHandle) -> float:
   return track.mixer_device.panning.value

def set_track_pan(track: TrackHandle, pan: float):
   track.mixer_device.panning.value = pan

def get_plugin(track: TrackHandle, name: str) -> PluginHandle:
   name_lower = name.lower()
   for device in track.devices:
      if device.name.lower() == name_lower:
         return device
   raise PluginNotFoundError(name)

def is_plugin_enabled(plugin: PluginHandle) -> bool:
   return get_parameter_value(get_parameter(plugin, 'Device On')) != 0

def set_plugin_enabled(plugin: PluginHandle, enabled: bool):
   set_parameter_value(get_parameter(plugin, 'Device On'), 1.0 if enabled else 0)

def get_parameter(plugin: PluginHandle, name: str) -> ParameterHandle:
   name_lower = name.lower()
   for param in plugin.parameters:
      if param.name.lower() == name_lower:
         return param
   raise ParameterNotFoundError(name)

def get_parameter_range(param: ParameterHandle) -> (float, float):
   return (param.min, param.max)

def get_parameter_value(param: ParameterHandle) -> float:
   return param.value

def set_parameter_value(param: ParameterHandle, value: float):
   param.value = value

def _get_document():
   return Live.Application.get_application().get_document()

def _vol_value_to_db(v: float) -> float:
   if v == 0:
      return -math.inf
   if v == 1.0:
      return 6.0
   return (-127.9278287 * pow(v, 4)
         +  390.2314102 * pow(v, 3)
         + -432.1372651 * pow(v, 2)
         +  244.6317808 * v
         + -68.70003194)

def _db_to_vol_value(v: float) -> float:
   if v == -math.inf:
      return 0
   if v == 6.0:
      return 1.0
   return (-9.867028203e-8    * pow(v, 4)
         + -0.000009835475566 * pow(v, 3)
         + -0.00001886034431  * pow(v, 2)
         +  0.02632908703     * v
         +  0.8496356422)

class DawscriptControlSurface(ControlSurface):

   def __init__(self, c_instance):
      super(DawscriptControlSurface, self).__init__(c_instance)
      self.events = list()
      self.request_rebuild_midi_map()
      dawscript = importlib.import_module('.dawscript', 'dawscript')
      dawscript.main({'control_surface':self})
      controller = load_controller()
      self.host_callback = controller.host_callback
      controller.on_project_load()

   def disconnect(self):
      super(DawscriptControlSurface, self).disconnect()

   def build_midi_map(self, midi_map_handle):
      script_handle = self._c_instance.handle()
      for ch in range (0, 16):
         for i in range(0, 128):
            Live.MidiMap.forward_midi_note(script_handle, midi_map_handle, ch, i)
            Live.MidiMap.forward_midi_cc(script_handle, midi_map_handle, ch, i)

   def receive_midi(self, midi_bytes):
      try:
         self.events.append(bytes(midi_bytes))
      except Exception as e:
         log(repr(e))

   def update_display(self):
      try:
         self.host_callback(self.events)
         self.events.clear()
      except Exception as e:
         log(repr(e))

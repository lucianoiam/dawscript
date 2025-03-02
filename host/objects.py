# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

from typing import Callable

import host
from host.types import ParameterHandle, PluginHandle, TrackHandle

class Host:
   def __new__(cls, *args, **kwargs):
      raise TypeError('Host class is not instantiable')

   @staticmethod
   def name() -> str:
      return host.name()

   @staticmethod
   def log(message: str):
      host.log(message)

class Parameter:
   def __init__(self, plugin: PluginHandle, name: str):
      self._handle = host.get_parameter(plugin, name)

   @property
   def range(self) -> (float, float):
      return host.get_parameter_range(self._handle)

   @property
   def value(self) -> float:
      return host.get_parameter_value(self._handle)

   @value.setter
   def value(self, value: float):
      host.set_parameter_value(self._handle, value)

   @property
   def value_listener(self) -> Callable[[float],None]:
      raise NotImplementedError

   @value_listener.setter
   def value_listener(self, callback: Callable[[float],None]):
      host.set_parameter_value_listener(self._handle, callback)

class Plugin:
   def __init__(self, track: TrackHandle, name: str):
      self._handle = host.get_plugin(track, name)

   @property
   def enabled(self) -> bool:
      return host.is_plugin_enabled(self._handle)

   @enabled.setter
   def enabled(self, value: bool):
      host.set_plugin_enabled(self._handle, value)

   @property
   def enabled_listener(self) -> Callable[[bool],None]:
      raise NotImplementedError

   @enabled_listener.setter
   def enabled_listener(self, callback: Callable[[bool],None]):
      host.set_plugin_enabled_listener(self._handle, callback)

   def toggle_enabled(self):
      host.toggle_plugin_enabled(self._handle)

   def parameter(self, name: str) -> Parameter:
      return Parameter(self._handle, name)

class Track:
   def __init__(self, name: str):
      self._handle = host.get_track(name)

   @property
   def mute(self) -> bool:
      return host.is_track_mute(self._handle)

   @mute.setter
   def mute(self, value: bool):
      host.set_track_mute(self._handle, value)

   @property
   def mute_listener(self) -> Callable[[bool],None]:
      raise NotImplementedError

   @mute_listener.setter
   def mute_listener(self, callback: Callable[[bool],None]):
      host.set_track_mute_listener(self._handle, callback)

   @property
   def volume_listener(self) -> Callable[[float],None]:
      raise NotImplementedError

   @volume_listener.setter
   def volume_listener(self, callback: Callable[[float],None]):
      host.set_track_volume_listener(self._handle, callback)

   def toggle_mute(self):
      host.toggle_track_mute(self._handle)

   @property
   def volume(self) -> float:
      return host.get_track_volume(self._handle)

   @volume.setter
   def volume(self, value: float):
      host.set_track_volume(self._handle, value)

   @property
   def pan(self) -> float:
      return host.get_track_pan(self._handle)

   @pan.setter
   def pan(self, value: float):
      host.set_track_pan(self._handle, value)

   @property
   def pan_listener(self) -> Callable[[float],None]:
      raise NotImplementedError

   @pan_listener.setter
   def pan_listener(self, callback: Callable[[float],None]):
      host.set_track_pan_listener(self._handle, callback)

   def plugin(self, name: str) -> Plugin:
      return Plugin(self._handle, name)

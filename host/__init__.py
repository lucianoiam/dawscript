# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

from .types import *

try:
   from .reaper import *
except IncompatibleEnvironmentError:
   pass

try:
   from .live import *
except IncompatibleEnvironmentError:
   pass

try:
   name()
except NameError:
   from .cli import *

def toggle_track_mute(track: TrackHandle):
   set_track_mute(track, not is_track_mute(track))

def toggle_track_mute_by_name(track: str):
   toggle_track_mute(get_track(track))

def toggle_plugin_enabled(plugin: PluginHandle):
   set_plugin_enabled(plugin, not is_plugin_enabled(plugin))

"""
def name() -> str
def main(context: Any)
def log(message: str)
def show_message(message: str)
def get_tracks() -> List[TrackHandle]
def get_track(name: str) -> TrackHandle
def is_track_mute(track: TrackHandle) -> bool
def set_track_mute(track: TrackHandle, mute: bool)
def add_track_mute_listener(track: TrackHandle, listener: Callable[[bool],None])
def del_track_mute_listener(track: TrackHandle, listener: Callable[[bool],None])
def get_track_volume(track: TrackHandle) -> float
def set_track_volume(track: TrackHandle, volume_db: float)
def add_track_volume_listener(track: TrackHandle, listener: Callable[[float],None])
def del_track_volume_listener(track: TrackHandle, listener: Callable[[float],None])
def get_track_pan(track: TrackHandle) -> float
def set_track_pan(track: TrackHandle, pan: float)
def add_track_pan_listener(track: TrackHandle, listener: Callable[[float],None])
def del_track_pan_listener(track: TrackHandle, listener: Callable[[float],None])
TODO: def get_plugins(track: TrackHandle) -> List[PluginHandle]
def get_plugin(track: TrackHandle, name: str) -> PluginHandle
def is_plugin_enabled(plugin: PluginHandle) -> bool
def set_plugin_enabled(plugin: PluginHandle, enabled: bool)
def add_plugin_enabled_listener(plugin: PluginHandle, listener: Callable[[bool],None])
def del_plugin_enabled_listener(plugin: PluginHandle, listener: Callable[[bool],None])
TODO: def get_parameters(plugin: PluginHandle) -> List[ParameterHandle]
def get_parameter(plugin: PluginHandle, name: str) -> ParameterHandle
def get_parameter_range(param: ParameterHandle) -> (float, float)
def get_parameter_value(param: ParameterHandle) -> float
def set_parameter_value(param: ParameterHandle, value: float)
def add_parameter_value_listener(param: ParameterHandle, listener: Callable[[float],None])
def del_parameter_value_listener(param: ParameterHandle, listener: Callable[[float],None])
"""

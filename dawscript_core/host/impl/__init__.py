# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

import importlib
from ..types import IncompatibleEnvironmentError


try:
    from .reaper import *
except IncompatibleEnvironmentError:
    pass
try:
    from .live import *
except IncompatibleEnvironmentError:
    pass
try:
    from .bitwig import *
except IncompatibleEnvironmentError:
    pass
try:
    name()
except NameError:
    from .cli import *


"""
def name() -> str
def main(controller: ModuleType, context: Any)
def log(message: str)
def display(message: str)
def get_object_id(handle: AnyHandle) -> str
def get_tracks() -> List[TrackHandle]
def get_track_type(track: TrackHandle) -> TrackType
def get_track_name(track: TrackHandle) -> str
def is_track_mute(track: TrackHandle) -> bool
def set_track_mute(track: TrackHandle, mute: bool)
def add_track_mute_listener(track: TrackHandle, listener: Callable[[bool],None])
def remove_track_mute_listener(track: TrackHandle, listener: Callable[[bool],None])
def get_track_volume(track: TrackHandle) -> float
def set_track_volume(track: TrackHandle, volume: float)
def add_track_volume_listener(track: TrackHandle, listener: Callable[[float],None])
def remove_track_volume_listener(track: TrackHandle, listener: Callable[[float],None])
def get_track_pan(track: TrackHandle) -> float
def set_track_pan(track: TrackHandle, pan: float)
def add_track_pan_listener(track: TrackHandle, listener: Callable[[float],None])
def remove_track_pan_listener(track: TrackHandle, listener: Callable[[float],None])
def get_track_plugins(track: TrackHandle) -> List[PluginHandle]
def get_plugin_name(plugin: PluginHandle) -> str
def is_plugin_enabled(plugin: PluginHandle) -> bool
def set_plugin_enabled(plugin: PluginHandle, enabled: bool)
def add_plugin_enabled_listener(plugin: PluginHandle, listener: Callable[[bool],None])
def remove_plugin_enabled_listener(plugin: PluginHandle, listener: Callable[[bool],None])
def get_plugin_parameters(plugin: PluginHandle) -> List[ParameterHandle]
def get_parameter_name(param: ParameterHandle) -> str
def get_parameter_range(param: ParameterHandle) -> (float, float)
def get_parameter_value(param: ParameterHandle) -> float
def set_parameter_value(param: ParameterHandle, value: float)
def add_parameter_value_listener(param: ParameterHandle, listener: Callable[[float],None])
def remove_parameter_value_listener(param: ParameterHandle, listener: Callable[[float],None])
"""

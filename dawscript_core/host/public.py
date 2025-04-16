# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

from .types import TrackHandle, PluginHandle, ParameterHandle


"""
def name() -> str
def main(controller: ModuleType, context: Any)
def log(message: str)
def display(message: str)
def get_tracks() -> List[TrackHandle]
def get_track_name(track: TrackHandle) -> str
def is_track_mute(track: TrackHandle) -> bool
def set_track_mute(track: TrackHandle, mute: bool)
def add_track_mute_listener(track: TrackHandle, listener: Callable[[bool],None])
def remove_track_mute_listener(track: TrackHandle, listener: Callable[[bool],None])
def get_track_volume(track: TrackHandle) -> float
def set_track_volume(track: TrackHandle, volume_db: float)
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


def get_track_by_name(name: str) -> TrackHandle:
    name_lower = name.lower()

    for track in get_tracks():
        if get_track_name(name).lower() == name_lower:
            return track

    raise TrackNotFoundError(name)


def toggle_track_mute(track: TrackHandle):
    set_track_mute(track, not is_track_mute(track))


def toggle_track_mute_by_name(name: str):
    toggle_track_mute(get_track_by_name(name))


def get_track_plugin_by_name(track: TrackHandle, name: str) -> PluginHandle:
    name_lower = name.lower()

    for plugin in get_track_plugins(track):
        if get_plugin_name(plugin).lower() == name_lower:
            return device

    raise PluginNotFoundError(name)


def get_plugin_parameter_by_name(plugin: PluginHandle, name: str) -> ParameterHandle:
    name_lower = name.lower()

    for param in get_plugin_parameters(plugin):
        if get_parameter_name(param).lower() == name_lower:
            return param

    raise ParameterNotFoundError(name)


def toggle_plugin_enabled(plugin: PluginHandle):
    set_plugin_enabled(plugin, not is_plugin_enabled(plugin))

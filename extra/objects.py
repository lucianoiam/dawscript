# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

from typing import Any, Callable, List

import host
from host.types import ParameterHandle, PluginHandle, TrackHandle


class Host:
    def __new__(cls, *args, **kwargs):
        raise TypeError("Host class is not instantiable")

    @staticmethod
    def name() -> str:
        return host.name()

    @staticmethod
    def log(message: str):
        host.log(message)

    @staticmethod
    def display(message: str):
        host.display(message)


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

    def add_value_listener(self, listener: Callable[[float], None]):
        host.add_parameter_value_listener(self._handle, listener)

    def del_value_listener(self, listener: Callable[[float], None]):
        host.del_parameter_value_listener(self._handle, listener)


class Plugin:
    def __init__(self, track: TrackHandle, name: str):
        self._handle = host.get_plugin(track, name)

    @property
    def enabled(self) -> bool:
        return host.is_plugin_enabled(self._handle)

    @enabled.setter
    def enabled(self, value: bool):
        host.set_plugin_enabled(self._handle, value)

    def add_enabled_listener(self, listener: Callable[[bool], None]):
        host.add_plugin_enabled_listener(self._handle, listener)

    def del_enabled_listener(self, listener: Callable[[bool], None]):
        host.del_plugin_enabled_listener(self._handle, listener)

    def toggle_enabled(self):
        host.toggle_plugin_enabled(self._handle)

    def parameter(self, name: str) -> Parameter:
        return Parameter(self._handle, name)


class Track:
    def __init__(self, name: str, **kwargs):
        if "handle" in kwargs:
            self._handle = kwargs["handle"]
        else:
            self._handle = host.get_track(name)

    @staticmethod
    def all() -> List[TrackHandle]:
        tracks = list()

        for handle in host.get_tracks():
            tracks.append(Track(handle=handle))

        return tracks

    @property
    def mute(self) -> bool:
        return host.is_track_mute(self._handle)

    @mute.setter
    def mute(self, value: bool):
        host.set_track_mute(self._handle, value)

    def add_mute_listener(self, listener: Callable[[bool], None]):
        host.add_track_mute_listener(self._handle, listener)

    def del_mute_listener(self, listener: Callable[[bool], None]):
        host.del_track_mute_listener(self._handle, listener)

    def add_volume_listener(self, listener: Callable[[float], None]):
        host.add_track_volume_listener(self._handle, listener)

    def del_volume_listener(self, listener: Callable[[float], None]):
        host.del_track_volume_listener(self._handle, listener)

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

    def add_pan_listener(self, listener: Callable[[float], None]):
        host.add_track_pan_listener(self._handle, listener)

    def del_pan_listener(self, listener: Callable[[float], None]):
        host.del_track_pan_listener(self._handle, listener)

    def plugin(self, name: str) -> Plugin:
        return Plugin(self._handle, name)

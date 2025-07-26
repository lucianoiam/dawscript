# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

from typing import Dict

from .impl import *
from .types import *


def get_fader_labels() -> Dict[int,float]:
    labels = {}

    for key, value in zip(CLIENT_VOL, HOST_VOL_DB):
        labels[key] = value

    return labels


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
            return plugin

    raise PluginNotFoundError(name)


def get_plugin_parameter_by_name(plugin: PluginHandle, name: str) -> ParameterHandle:
    name_lower = name.lower()

    for param in get_plugin_parameters(plugin):
        if get_parameter_name(param).lower() == name_lower:
            return param

    raise ParameterNotFoundError(name)


def toggle_plugin_enabled(plugin: PluginHandle):
    set_plugin_enabled(plugin, not is_plugin_enabled(plugin))

# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

from types import ModuleType
from typing import Any, Callable, List

from .types import (
	IncompatibleEnvironmentError,
    ParameterHandle,
    ParameterNotFoundError,
    PluginHandle,
    PluginNotFoundError,
    TrackHandle,
    TrackNotFoundError,
    TrackType
)

# TODO - if cannot connect to bitwig server throw IncompatibleEnvironmentError
raise IncompatibleEnvironmentError


def name() -> str:
	return "bitwig"


def main(controller: ModuleType, context: Any):
	pass


def log(message: str):
	pass


def display(message: str):
	pass


def get_tracks() -> List[TrackHandle]:
	pass


def get_track_type(track: TrackHandle) -> TrackType:
	pass


def get_track_name(track: TrackHandle) -> str:
	pass


def is_track_mute(track: TrackHandle) -> bool:
	pass


def set_track_mute(track: TrackHandle, mute: bool):
	pass


def add_track_mute_listener(track: TrackHandle, listener: Callable[[bool],None]):
	pass


def remove_track_mute_listener(track: TrackHandle, listener: Callable[[bool],None]):
	pass


def get_track_volume(track: TrackHandle) -> float:
	pass


def set_track_volume(track: TrackHandle, volume_db: float):
	pass


def add_track_volume_listener(track: TrackHandle, listener: Callable[[float],None]):
	pass


def remove_track_volume_listener(track: TrackHandle, listener: Callable[[float],None]):
	pass


def get_track_pan(track: TrackHandle) -> float:
	pass


def set_track_pan(track: TrackHandle, pan: float):
	pass


def add_track_pan_listener(track: TrackHandle, listener: Callable[[float],None]):
	pass


def remove_track_pan_listener(track: TrackHandle, listener: Callable[[float],None]):
	pass


def get_track_plugins(track: TrackHandle) -> List[PluginHandle]:
	pass


def get_plugin_name(plugin: PluginHandle) -> str:
	pass


def is_plugin_enabled(plugin: PluginHandle) -> bool:
	pass


def set_plugin_enabled(plugin: PluginHandle, enabled: bool):
	pass


def add_plugin_enabled_listener(plugin: PluginHandle, listener: Callable[[bool],None]):
	pass


def remove_plugin_enabled_listener(plugin: PluginHandle, listener: Callable[[bool],None]):
	pass


def get_plugin_parameters(plugin: PluginHandle) -> List[ParameterHandle]:
	pass


def get_parameter_name(param: ParameterHandle) -> str:
	pass


def get_parameter_range(param: ParameterHandle) -> (float, float):
	pass


def get_parameter_value(param: ParameterHandle) -> float:
	pass


def set_parameter_value(param: ParameterHandle, value: float):
	pass


def add_parameter_value_listener(param: ParameterHandle, listener: Callable[[float],None]):
	pass


def remove_parameter_value_listener(param: ParameterHandle, listener: Callable[[float],None]):
	pass

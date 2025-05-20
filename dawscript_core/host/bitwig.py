# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

import time
from types import ModuleType
from typing import Any, Callable, Dict, List

from .types import (
    ALL_MIDI_INPUTS,
    IncompatibleEnvironmentError,
    ParameterHandle,
    ParameterNotFoundError,
    PluginHandle,
    PluginNotFoundError,
    TrackHandle,
    TrackNotFoundError,
    TrackType
)

from py4j.java_gateway import JavaGateway, CallbackServerParameters, GatewayParameters, Py4JNetworkError


try:
    gateway = JavaGateway(
        gateway_parameters=GatewayParameters(auto_convert=True),
        callback_server_parameters=CallbackServerParameters()
    )
    gateway.jvm.java.lang.System.getProperty("java.version")
    bwextension = gateway.entry_point
except Py4JNetworkError:
    raise IncompatibleEnvironmentError


def name() -> str:
    return "bitwig"


def main(controller: ModuleType, context: Any):
    bwextension.setController(ControllerBridge(controller))
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass


def log(message: str):
    pass


def display(message: str):
    _host().showPopupNotification(message)


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


def _host():
    return bwextension.getHost()


class ControllerBridge:
    def __init__(self, controller: ModuleType):
        self.controller = controller

    def get_config(self):
        jconfig = gateway.jvm.java.util.HashMap()
        try:
            config = self.controller.get_config()
            jconfig.put("midi_inputs", config.midi_inputs)
        except AttributeError:
            jconfig.put("midi_inputs", ALL_MIDI_INPUTS)
        return jconfig

    def on_script_start(self):
        try:
            self.controller.on_script_start()
        except AttributeError:
            pass

    def on_script_stop(self):
        try:
            self.controller.on_script_stop()
        except AttributeError:
            pass

    def on_project_load(self):
        try:
            self.controller.on_project_load()
        except AttributeError:
            pass

    def host_callback(self, midi: List[bytes]):
        try:
            self.controller.host_callback(midi)
        except AttributeError:
            pass

    class Java:
        implements = ["dawscript.ControllerBridge"]

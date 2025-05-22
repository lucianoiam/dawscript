# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

import math
import sys
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
    bw_ext = gateway.entry_point
except Py4JNetworkError:
    raise IncompatibleEnvironmentError


def name() -> str:
    return "bitwig"


def main(controller: ModuleType, context: Any):
    bw_ext.setController(Controller(controller))
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        gateway.shutdown()


def log(message: str):
    bw_ext.getHost().errorln(str(message))


def display(message: str):
    bw_ext.getHost().showPopupNotification(str(message))


def get_tracks() -> List[TrackHandle]:
    tracks = []
    bank = bw_ext.getProjectTrackBank()
    for i in range(0, bank.itemCount().get()):
        tracks.append(bank.getItemAt(i))
    return tracks


def get_track_type(track: TrackHandle) -> TrackType:
    return TrackType.OTHER # TODO


def get_track_name(track: TrackHandle) -> str:
    return track.name().get()


def is_track_mute(track: TrackHandle) -> bool:
    return False # TODO


def set_track_mute(track: TrackHandle, mute: bool):
    pass # TODO


def add_track_mute_listener(track: TrackHandle, listener: Callable[[bool],None]):
    pass # TODO


def remove_track_mute_listener(track: TrackHandle, listener: Callable[[bool],None]):
    pass # TODO


def get_track_volume(track: TrackHandle) -> float:
    return _vol_value_to_db(track.volume().get())


def set_track_volume(track: TrackHandle, volume_db: float):
    track.volume().setImmediately(_db_to_vol_value(volume_db))


def add_track_volume_listener(track: TrackHandle, listener: Callable[[float],None]):
    _add_listener(track, "volume", listener, get_track_volume)


def remove_track_volume_listener(track: TrackHandle, listener: Callable[[float],None]):
    _remove_listener(track, "volume", listener)


def get_track_pan(track: TrackHandle) -> float:
    return 0.0 # TODO


def set_track_pan(track: TrackHandle, pan: float):
    pass # TODO


def add_track_pan_listener(track: TrackHandle, listener: Callable[[float],None]):
    pass # TODO


def remove_track_pan_listener(track: TrackHandle, listener: Callable[[float],None]):
    pass # TODO


def get_track_plugins(track: TrackHandle) -> List[PluginHandle]:
    return [] # TODO


def get_plugin_name(plugin: PluginHandle) -> str:
    return '' # TODO


def is_plugin_enabled(plugin: PluginHandle) -> bool:
    return False # TODO


def set_plugin_enabled(plugin: PluginHandle, enabled: bool):
    pass # TODO


def add_plugin_enabled_listener(plugin: PluginHandle, listener: Callable[[bool],None]):
    pass # TODO


def remove_plugin_enabled_listener(plugin: PluginHandle, listener: Callable[[bool],None]):
    pass # TODO


def get_plugin_parameters(plugin: PluginHandle) -> List[ParameterHandle]:
    return [] # TODO


def get_parameter_name(param: ParameterHandle) -> str:
    return '' # TODO


def get_parameter_range(param: ParameterHandle) -> (float, float):
    return (0.0, 1.0) # TODO


def get_parameter_value(param: ParameterHandle) -> float:
    return 1.0 # TODO


def set_parameter_value(param: ParameterHandle, value: float):
    pass # TODO


def add_parameter_value_listener(param: ParameterHandle, listener: Callable[[float],None]):
    pass # TODO


def remove_parameter_value_listener(param: ParameterHandle, listener: Callable[[float],None]):
    pass # TODO


def _add_listener(target: Any, prop: str, listener: Callable, getter: Callable):
    def bound_getter():
        return getter(target)

    runnable = PythonRunnable(lambda: listener(bound_getter()))
    bw_ext.addListener(target, prop, id(listener), runnable)


def _remove_listener(target: Any, prop: str, listener: Callable):
    bw_ext.removeListener(target, prop, id(listener))


def _vol_value_to_db(v: float) -> float:
    if v == 0:
        return -math.inf
    if v >= 1.0:
        return 6.0
    return (
        -127.9278287 * pow(v, 4)
        + 390.2314102 * pow(v, 3)
        + -432.1372651 * pow(v, 2)
        + 244.6317808 * v
        + -68.70003194
    )


def _db_to_vol_value(v: float) -> float:
    if v == -math.inf:
        return 0
    if v >= 6.0:
        return 1.0
    vol = (
        -9.867028203e-8 * pow(v, 4)
        + -0.000009835475566 * pow(v, 3)
        + -0.00001886034431 * pow(v, 2)
        + 0.02632908703 * v
        + 0.8496356422
    )

    return float(max(0, vol))


class Controller:
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
        implements = ["dawscript.Controller"]


class PythonRunnable:
    def __init__(self, callback: Callable):
        self.callback = callback

    def run(self):
        self.callback()

    class Java:
        implements = ["dawscript.PythonRunnable"]

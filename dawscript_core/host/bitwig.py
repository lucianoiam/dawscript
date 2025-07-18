# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

import math
import sys
import time
from types import ModuleType
from typing import Any, Callable, Dict, List

from .types import (
    ALL_MIDI_INPUTS,
    AnyHandle,
    IncompatibleEnvironmentError,
    ParameterHandle,
    ParameterNotFoundError,
    PluginHandle,
    PluginNotFoundError,
    TrackHandle,
    TrackNotFoundError,
    TrackType
)

try:
    from py4j.java_gateway import JavaGateway, CallbackServerParameters, GatewayParameters, Py4JNetworkError
except ModuleNotFoundError:
    # fails to import on Live
    raise IncompatibleEnvironmentError

if len(sys.argv) < 2:
    raise IncompatibleEnvironmentError

try:
    port = int(sys.argv[1])
    gateway = JavaGateway(
        gateway_parameters=GatewayParameters(
            port=port,
            auto_convert=True
        ),
        callback_server_parameters=CallbackServerParameters(port=port + 1)
    )
    gateway.jvm.java.lang.System.getProperty("java.version")
    bw_ext = gateway.entry_point
except Py4JNetworkError as e:
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


# ~/Library/Logs/Bitwig/BitwigStudio.log 
def log(message: str):
    bw_ext.getHost().errorln(str(message))


def display(message: str):
    bw_ext.getHost().showPopupNotification(str(message))


def get_object_id(handle: AnyHandle) -> str:
    return f"{handle.hashCode() & 0xFFFFFFFF:08x}"


def get_tracks() -> List[TrackHandle]:
    tracks = []
    bank = bw_ext.getTrackBank()
    for i in range(0, bank.itemCount().get()):
        tracks.append(bank.getItemAt(i))
    return tracks


def get_track_type(track: TrackHandle) -> TrackType:
    track_type = track.trackType().get()
    if track_type == 'Audio':
        return TrackType.AUDIO
    elif track_type == 'Instrument':
        return TrackType.MIDI
    return TrackType.OTHER


def get_track_name(track: TrackHandle) -> str:
    return track.name().get()


def is_track_mute(track: TrackHandle) -> bool:
    return track.mute().get()


def set_track_mute(track: TrackHandle, mute: bool):
    track.mute().set(mute)


def add_track_mute_listener(track: TrackHandle, listener: Callable[[bool],None]):
    _add_listener(track, "mute", listener, is_track_mute)


def remove_track_mute_listener(track: TrackHandle, listener: Callable[[bool],None]):
    _remove_listener(track, "mute", listener)


def get_track_volume(track: TrackHandle) -> float:
    return _vol_value_to_db(track.volume().get())


def set_track_volume(track: TrackHandle, volume_db: float):
    track.volume().setImmediately(_db_to_vol_value(volume_db))


def add_track_volume_listener(track: TrackHandle, listener: Callable[[float],None]):
    _add_listener(track, "volume", listener, get_track_volume)


def remove_track_volume_listener(track: TrackHandle, listener: Callable[[float],None]):
    _remove_listener(track, "volume", listener)


def get_track_pan(track: TrackHandle) -> float:
    return 2.0 * track.pan().get() - 1.0


def set_track_pan(track: TrackHandle, pan: float):
    track.pan().setImmediately((float(pan) + 1.0) / 1.0)


def add_track_pan_listener(track: TrackHandle, listener: Callable[[float],None]):
    _add_listener(track, "pan", listener, get_track_pan)


def remove_track_pan_listener(track: TrackHandle, listener: Callable[[float],None]):
    _remove_listener(track, "pan", listener)


def get_track_plugins(track: TrackHandle) -> List[PluginHandle]:
    plugins = []
    bank = bw_ext.getTrackDeviceBank(track)
    for i in range(0, bank.itemCount().get()):
        plugins.append(bank.getItemAt(i))
    return plugins


def get_plugin_name(plugin: PluginHandle) -> str:
    return plugin.name().get()


def is_plugin_enabled(plugin: PluginHandle) -> bool:
    return plugin.isEnabled().get()


def set_plugin_enabled(plugin: PluginHandle, enabled: bool):
    plugin.isEnabled().set(enabled)


def add_plugin_enabled_listener(plugin: PluginHandle, listener: Callable[[bool],None]):
    _add_listener(plugin, "enabled", listener, is_plugin_enabled)


def remove_plugin_enabled_listener(plugin: PluginHandle, listener: Callable[[bool],None]):
    _remove_listener(plugin, "enabled", listener)


def get_plugin_parameters(plugin: PluginHandle) -> List[ParameterHandle]:
    parameters = []
    bank = bw_ext.getPluginParameterBank(plugin)
    for i in range(0, bank.getParameterCount()):
        param = bank.getParameter(i)
        if param.name().get():
            parameters.append(param)
    return parameters


def get_parameter_name(param: ParameterHandle) -> str:
    return param.name().get()


def get_parameter_range(param: ParameterHandle) -> (float, float):
    return tuple(bw_ext.getParameterRange(param))


def get_parameter_value(param: ParameterHandle) -> float:
    return param.value().getRaw()


def set_parameter_value(param: ParameterHandle, value: float):
    param.value().setRaw(float(value))


def add_parameter_value_listener(param: ParameterHandle, listener: Callable[[float],None]):
    _add_listener(param, "value", listener, get_parameter_value)


def remove_parameter_value_listener(param: ParameterHandle, listener: Callable[[float],None]):
    _remove_listener(param, "value", listener)


def _add_listener(target: Any, prop: str, listener: Callable, getter: Callable):
    def bound_getter():
        return getter(target)

    runnable = PythonRunnable(lambda: listener(bound_getter()))
    bw_ext.addListener(target, prop, id(listener), runnable)


def _remove_listener(target: Any, prop: str, listener: Callable):
    bw_ext.removeListener(target, prop, id(listener))


def _vol_value_to_db(v: float) -> float:
    if v <= 0:
        return -math.inf
    if v >= 1.0:
        return 6.0
    a = -128.3272282
    b = 25.53989661
    c = 96.22932269
    d = -0.05850250872
    e = 10787.4341
    return a + b * math.asinh(c * v + d * math.asinh(e * v))


def _db_to_vol_value(v: float) -> float:
    if v == -math.inf:
        return 0
    if v >= 6.0:
        return 1.0
    a = 0.004374052017
    b = 0.7891697633
    c = 0.000054132527
    d = 1.039281072
    return a + b * (d ** v) + c * v


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

# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

import sys
import time
from types import ModuleType
from typing import Any, Callable, Dict, List

from .util import map_interp
from ..types import (
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
    bw_ext_class = gateway.jvm.dawscript.DawscriptExtension;
    bw_ext = gateway.entry_point
except Py4JNetworkError as e:
    raise IncompatibleEnvironmentError

N_INF = float('-inf')
HOST_VOL_DB = [N_INF,   -36,   -24,   -18,   -12,    -6,     0,     6]
HOST_VOL    = [0.000, 0.200, 0.316, 0.398, 0.500, 0.630, 0.793, 1.000]
CLIENT_VOL  = [0.000, 0.226, 0.396, 0.491, 0.623, 0.755, 0.887, 1.000]


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


def get_stable_object_id(handle: AnyHandle) -> str:
    return f"{bw_ext_class.getStableObjectId(handle) & 0xFFFFFFFF:08x}"


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
    return map_interp(track.volume().get(), HOST_VOL, CLIENT_VOL)


def set_track_volume(track: TrackHandle, volume: float):
    track.volume().setImmediately(map_interp(volume, CLIENT_VOL, HOST_VOL))


def add_track_volume_listener(track: TrackHandle, listener: Callable[[float],None]):
    _add_listener(track, "volume", listener, get_track_volume)


def remove_track_volume_listener(track: TrackHandle, listener: Callable[[float],None]):
    _remove_listener(track, "volume", listener)


def get_track_pan(track: TrackHandle) -> float:
    return 2.0 * track.pan().get() - 1.0


def set_track_pan(track: TrackHandle, pan: float):
    track.pan().setImmediately((float(pan) + 1.0) / 2.0)


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

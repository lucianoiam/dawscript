# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

import math
import sys
from types import ModuleType
from typing import Any, Callable, Dict, List

from .types import (
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
    import Live
    from _Framework.ControlSurface import ControlSurface
except ModuleNotFoundError:
    raise IncompatibleEnvironmentError

_control_surface = None


def name() -> str:
    return "live"


def main(controller: ModuleType, context: Any):
    global _control_surface
    _control_surface = context
    _control_surface.set_controller(controller)


# ~/Library/Preferences/Ableton/Live\ x.x.x/Log.txt
def log(message: str):
    if _control_surface is not None:
        _control_surface.log_message(str(message))
    else:
        print(message, file=sys.stderr)


def display(message: str):
    if _control_surface is not None:
        _control_surface.show_message(str(message))
    else:
        print(message, file=sys.stderr)


def get_object_id(handle: AnyHandle) -> str:
    if isinstance(handle, Live.Track.Track):
        # Combine name and color_index to reduce collision risk
        return f"{_d2b_hash(handle.name + str(handle.color_index)):08x}"
    elif isinstance(handle, Live.Device.Device):
        # Use parent track's name hash, device name, and index for uniqueness
        track = handle.canonical_parent
        track_id = _d2b_hash(track.name + str(track.color_index))
        device_n = list(track.devices).index(handle)
        return f"{track_id:08x}/{_d2b_hash(handle.name):08x}_{device_n}"
    elif isinstance(handle, Live.DeviceParameter.DeviceParameter):
        # Use parent device's ID and parameter name for uniqueness
        device = handle.canonical_parent
        track = device.canonical_parent
        track_id = _d2b_hash(track.name + str(track.color_index))
        device_n = list(track.devices).index(device)
        device_id = f"{track_id:08x}/{_d2b_hash(device.name):08x}/{device_n}"
        return f"{device_id}/{_d2b_hash(handle.name):08x}"

    return None


def get_tracks() -> List[TrackHandle]:
    return list(_get_document().tracks)


def get_track_type(track: TrackHandle) -> TrackType:
    if track in _control_surface.song().return_tracks or track.is_foldable:
        return TrackType.OTHER
    elif track.has_midi_input:
        return TrackType.MIDI
    else:
        return TrackType.AUDIO


def get_track_name(track: TrackHandle) -> str:
    return track.name


def is_track_mute(track: TrackHandle) -> bool:
    return track.mute


def set_track_mute(track: TrackHandle, mute: bool):
    track.mute = mute


def add_track_mute_listener(track: TrackHandle, listener: Callable[[bool], None]):
    _control_surface.add_listener(
        track,
        "mute",
        listener,
        is_track_mute,
        track.add_mute_listener,
        track.remove_mute_listener,
    )


def remove_track_mute_listener(track: TrackHandle, listener: Callable[[bool], None]):
    _control_surface.remove_listener(track, "mute", listener)


def get_track_volume(track: TrackHandle) -> float:
    return _vol_value_to_db(track.mixer_device.volume.value)


def set_track_volume(track: TrackHandle, volume_db: float):
    track.mixer_device.volume.value = _db_to_vol_value(volume_db)


def add_track_volume_listener(track: TrackHandle, listener: Callable[[float], None]):
    _control_surface.add_listener(
        track,
        "volume",
        listener,
        get_track_volume,
        track.mixer_device.volume.add_value_listener,
        track.mixer_device.volume.remove_value_listener,
    )


def remove_track_volume_listener(track: TrackHandle, listener: Callable[[float], None]):
    _control_surface.remove_listener(track, "volume", listener)


def get_track_pan(track: TrackHandle) -> float:
    return track.mixer_device.panning.value


def set_track_pan(track: TrackHandle, pan: float):
    track.mixer_device.panning.value = pan


def add_track_pan_listener(track: TrackHandle, listener: Callable[[float], None]):
    _control_surface.add_listener(
        track,
        "pan",
        listener,
        get_track_pan,
        track.mixer_device.panning.add_value_listener,
        track.mixer_device.panning.remove_value_listener,
    )


def remove_track_pan_listener(track: TrackHandle, listener: Callable[[float], None]):
    _control_surface.remove_listener(track, "pan", listener)


def get_track_plugins(track: TrackHandle) -> List[PluginHandle]:
    return list(track.devices)


def get_plugin_name(plugin: PluginHandle) -> str:
    return plugin.name


def is_plugin_enabled(plugin: PluginHandle) -> bool:
    return get_parameter_value(_get_parameter_device_on(plugin)) != 0


def set_plugin_enabled(plugin: PluginHandle, enabled: bool):
    set_parameter_value(_get_parameter_device_on(plugin), 1.0 if enabled else 0)


def add_plugin_enabled_listener(plugin: PluginHandle, listener: Callable[[bool], None]):
    device_on = _get_parameter_device_on(plugin)
    _control_surface.add_listener(
        plugin,
        "enabled",
        listener,
        is_plugin_enabled,
        device_on.add_value_listener,
        device_on.remove_value_listener,
    )


def remove_plugin_enabled_listener(plugin: PluginHandle, listener: Callable[[bool], None]):
    device_on = _get_parameter_device_on(plugin)
    _control_surface.remove_listener(plugin, "enabled", listener)


def get_plugin_parameters(plugin: PluginHandle) -> List[ParameterHandle]:
    return list(plugin.parameters)


def get_parameter_name(param: ParameterHandle) -> str:
    return param.name


def get_parameter_range(param: ParameterHandle) -> (float, float):
    return (param.min, param.max)


def get_parameter_value(param: ParameterHandle) -> float:
    return param.value


def set_parameter_value(param: ParameterHandle, value: float):
    param.value = value


def add_parameter_value_listener(
    param: ParameterHandle, listener: Callable[[float], None]
):
    _control_surface.add_listener(
        param,
        "value",
        listener,
        get_parameter_value,
        param.add_value_listener,
        param.remove_value_listener,
    )


def remove_parameter_value_listener(
    param: ParameterHandle, listener: Callable[[float], None]
):
    _control_surface.remove_listener(param, "value", listener)


def _get_document():
    return Live.Application.get_application().get_document()


def _get_parameter_device_on(plugin: PluginHandle) -> ParameterHandle:
    return get_plugin_parameter_by_name(plugin, "Device On")


def _d2b_hash(string):
    hash_value = 0
    for char in string:
        hash_value = (31 * hash_value + ord(char)) & 0xFFFFFFFF
    return hash_value


def _vol_value_to_db(v: float) -> float:
    if v <= 0:
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

    return max(0, vol)


class DawscriptControlSurface(ControlSurface):

    suggested_update_time_in_ms = 16

    def __init__(self, c_instance):
        super(DawscriptControlSurface, self).__init__(c_instance)

        self._cleanup_cb: Dict[Any, Callable] = {}
        self._events: List[bytes] = []
        self._deferred: List[Callable] = []

        self.request_rebuild_midi_map()

    def build_midi_map(self, midi_map_handle):
        script_handle = self._c_instance.handle()

        for ch in range(0, 16):
            for i in range(0, 128):
                Live.MidiMap.forward_midi_note(script_handle, midi_map_handle, ch, i)
                Live.MidiMap.forward_midi_cc(script_handle, midi_map_handle, ch, i)

    def receive_midi(self, midi_bytes):
        try:
            self._events.append(bytes(midi_bytes))
        except Exception as e:
            log(repr(e))

    def update_display(self):
        for func in self._deferred:
            try:
                func()
            except Exception as e:
                log(repr(e))

        self._deferred.clear()

        try:
            host_callback = self._controller.host_callback
        except AttributeError:
            return

        try:
            host_callback(self._events)
        except Exception as e:
            log(repr(e))

        self._events.clear()

    def disconnect(self):
        try:
            self._controller.on_script_stop()
        except AttributeError:
            pass

        for callback in self._cleanup_cb.values():
            callback()

        super(DawscriptControlSurface, self).disconnect()

    def set_controller(self, controller):
        self._controller = controller

        try:
            self._controller.on_script_start()
        except AttributeError:
            pass

        try:
            # ControlSurface is reinstantiated every time a project is loaded
            self._controller.on_project_load()
        except AttributeError:
            pass

    def add_listener(self, target, prop, listener, getter, add_func, remove_func):
        key_tp = f"{target}_{prop}"

        def bound_getter():
            return getter(target)

        def def_listener():
            # Changes cannot be triggered by notifications. You will need to defer your response.
            return self._deferred.append(lambda: listener(bound_getter()))

        self._cleanup_cb[key_tp] = lambda: remove_func(def_listener)
        add_func(def_listener)

    def remove_listener(self, target, prop, listener):
        key_tp = f"{target}_{prop}"

        self._cleanup_cb[key_tp]()
        del self._cleanup_cb[key_tp]

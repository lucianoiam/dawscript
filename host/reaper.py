# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

from .types import IncompatibleEnvironmentError

try:
    from reaper_python import (
        RPR_GetMIDIInputName,
        RPR_GetTrack,
        RPR_GetTrackName,
        RPR_GetTrackUIMute,
        RPR_SetTrackUIMute,
        RPR_GetTrackUIVolPan,
        RPR_SetTrackUIVolume,
        RPR_SetTrackUIPan,
        RPR_TrackFX_GetByName,
        RPR_TrackFX_GetFXName,
        RPR_TrackFX_GetCount,
        RPR_TrackFX_GetEnabled,
        RPR_TrackFX_SetEnabled,
        RPR_TrackFX_GetNumParams,
        RPR_TrackFX_GetParamName,
        RPR_TrackFX_GetParam,
        RPR_TrackFX_SetParam,
        RPR_GetProjectPath,
        RPR_ShowConsoleMsg,
        rpr_getfp,
        rpr_packs,
        rpr_unpacks,
    )
except ModuleNotFoundError:
    raise IncompatibleEnvironmentError

import math
import sys
from ctypes import *
from typing import Any, Callable, Dict, List

from .private import load_controller
from .types import (
    ParameterHandle,
    ParameterNotFoundError,
    PluginHandle,
    PluginNotFoundError,
    TrackHandle,
    TrackNotFoundError,
)

RPR_defer = None
_controller = None
_proj_path = None
_event_n = 0
_listeners: Dict[str, List[Callable]] = {}
_getters: Dict[str, Callable] = {}
_state: Dict[str, Any] = {}


def name() -> str:
    return "reaper"


def main(context: Any):
    global RPR_defer, _controller

    RPR_atexit = context["RPR_atexit"]
    RPR_defer = context["RPR_defer"]
    _controller = load_controller()

    RPR_atexit("from host import reaper; reaper.cleanup()")

    try:
        _controller.on_script_start()
    except AttributeError:
        pass

    _tick()


def cleanup():
    global _controller, _proj_path, _event_n

    try:
        _controller.on_script_stop()
    except AttributeError:
        pass

    _controller = None
    _proj_path = None
    _event_n = 0
    _listeners.clear()
    _getters.clear()
    _state.clear()


def log(message: str):
    print(message, file=sys.stderr)


def display(message: str):
    RPR_ShowConsoleMsg(f"{message}\n")


def get_tracks() -> List[TrackHandle]:
    tracks = list()
    i = 0

    while True:
        track = RPR_GetTrack(0, i)
        i += 1

        if track == "(MediaTrack*)0x0000000000000000":
            break

        tracks.append(track)

    return tracks


def get_track(name: str) -> TrackHandle:
    name_lower = name.lower()

    for track in get_tracks():
        if RPR_GetTrackName(track, "", 32)[2].lower() == name_lower:
            return track

    raise TrackNotFoundError(name)


def get_track_name(track: TrackHandle) -> str:
    return 'FIXME'


def is_track_mute(track: TrackHandle) -> bool:
    return RPR_GetTrackUIMute(track, False)[2] == 1


def set_track_mute(track: TrackHandle, mute: bool):
    RPR_SetTrackUIMute(track, mute, 0)


def add_track_mute_listener(track: TrackHandle, listener: Callable[[bool], None]):
    _add_listener(track, "mute", listener, is_track_mute)


def del_track_mute_listener(track: TrackHandle, listener: Callable[[bool], None]):
    _del_listener(track, "mute", listener)


def get_track_volume(track: TrackHandle) -> float:
    return _vol_value_to_db(RPR_GetTrackUIVolPan(track, 0.0, 0.0)[2])


def set_track_volume(track: TrackHandle, volume_db: float):
    RPR_SetTrackUIVolume(track, _db_to_vol_value(volume_db), False, False, 0)


def add_track_volume_listener(track: TrackHandle, listener: Callable[[float], None]):
    _add_listener(track, "volume", listener, get_track_volume)


def del_track_volume_listener(track: TrackHandle, listener: Callable[[float], None]):
    _del_listener(track, "volume", listener)


def get_track_pan(track: TrackHandle) -> float:
    return RPR_GetTrackUIVolPan(track, 0.0, 0.0)[3]


def add_track_pan_listener(track: TrackHandle, listener: Callable[[float], None]):
    _add_listener(track, "pan", listener, get_track_pan)


def del_track_pan_listener(track: TrackHandle, listener: Callable[[float], None]):
    _del_listener(track, "pan", listener)


def set_track_pan(track: TrackHandle, pan: float):
    RPR_SetTrackUIPan(track, pan, False, False, 0)


def get_track_plugins(track: TrackHandle) -> List[PluginHandle]:
    return list(range(0, RPR_TrackFX_GetCount(track)))


def get_track_plugin(track: TrackHandle, name: str) -> PluginHandle:
    plugin = RPR_TrackFX_GetByName(track, name, False)

    if plugin == -1:
        raise PluginNotFoundError(name)

    return (track, plugin)


def get_plugin_name(plugin: PluginHandle) -> str:
    return 'FIXME'


def is_plugin_enabled(plugin: PluginHandle) -> bool:
    return RPR_TrackFX_GetEnabled(*plugin) == 1


def set_plugin_enabled(plugin: PluginHandle, enabled: bool):
    RPR_TrackFX_SetEnabled(*plugin, enabled)


def add_plugin_enabled_listener(plugin: PluginHandle, listener: Callable[[bool], None]):
    _add_listener(plugin, "enabled", listener, is_plugin_enabled)


def del_plugin_enabled_listener(plugin: PluginHandle, listener: Callable[[bool], None]):
    _del_listener(plugin, "enabled", listener)


def get_plugin_parameters(plugin: PluginHandle) -> List[ParameterHandle]:
    return [] # FIXME


def get_plugin_parameter(plugin: PluginHandle, name: str) -> ParameterHandle:
    name_lower = name.lower()
    num = RPR_TrackFX_GetNumParams(*plugin)

    for i in range(0, num):
        if RPR_TrackFX_GetParamName(*plugin, i, "", 32)[4].lower() == name_lower:
            return (*plugin, i)

    raise ParameterNotFoundError(name)


def get_parameter_name(param: ParameterHandle) -> str:
    return 'FIXME'


def get_parameter_range(param: ParameterHandle) -> (float, float):
    result = RPR_TrackFX_GetParam(*param, 0.0, 0.0)
    return (result[4], result[5])


def get_parameter_value(param: ParameterHandle) -> float:
    return RPR_TrackFX_GetParam(*param, 0.0, 0.0)[0]


def set_parameter_value(param: ParameterHandle, value: float):
    RPR_TrackFX_SetParam(*param, value)


def add_parameter_value_listener(
    param: ParameterHandle, listener: Callable[[float], None]
):
    _add_listener(param, "value", listener, get_parameter_value)


def del_parameter_value_listener(
    param: ParameterHandle, listener: Callable[[float], None]
):
    _del_listener(param, "value", listener)


TWENTY_OVER_LN10 = 8.6858896380650365530225783783321
LN10_OVER_TWENTY = 0.11512925464970228420089957273422


def _vol_value_to_db(v: float) -> float:
    if v < 0.0000000298023223876953125:
        return -math.inf
    v = TWENTY_OVER_LN10 * math.log(v)
    if v <= -150.0:
        return -math.inf
    else:
        return v


def _db_to_vol_value(v: float) -> float:
    return math.exp(LN10_OVER_TWENTY * v)


def _tick():
    global _proj_path

    try:
        _call_listeners()

        try:
            # Ignore default startup project when running as a global script
            proj_path = RPR_GetProjectPath("", 256)[0]
            if _proj_path != proj_path and not proj_path.endswith("REAPER Media"):
                _proj_path = proj_path
                _controller.on_project_load()
        except AttributeError:
            pass
        try:
            _controller.host_callback(_read_midi_events())
        except AttributeError:
            pass
    except Exception as e:
        log(repr(e))

    RPR_defer("from host import reaper; reaper._tick()")


def _read_midi_events():
    global _event_n
    events = list()
    i = 0

    while True:
        event = RPR_MIDI_GetRecentInputEvent(i, None, 3, 0, 0, 0.0, 0)
        if event[0] <= _event_n:
            break

        _event_n = event[0]
        i += 1

        accept: bool

        try:
            if _controller.config.midi_inputs:
                event_midi_in = RPR_GetMIDIInputName(event[5], None, 32)[2].lower()
                midi_ins = [name.lower() for name in _controller.config.midi_inputs]
                accept = any(map(lambda midi_in: midi_in in event_midi_in, midi_ins))
            else:
                accept = True
        except AttributeError:
            pass

        if accept:
            events.append(bytes(event[2]))

    return events


def _add_listener(target: Any, prop: str, listener: Callable, getter: Callable):
    key_tp = f"{target}_{prop}"

    def target_getter():
        return getter(target)

    if key_tp not in _listeners:
        _listeners[key_tp] = []
        _getters[key_tp] = target_getter
        _state[key_tp] = target_getter()

    _listeners[key_tp].append(listener)


def _del_listener(target: Any, prop: str, listener: Callable):
    key_tp = f"{target}_{prop}"

    _listeners[key_tp] = [l for l in _listeners[key_tp] if l != listener]

    if not _listeners[key_tp]:
        del _listeners[key_tp]
        del _getters[key_tp]
        del _state[key_tp]


def _call_listeners():
    for key_tp, getter in _getters.items():
        now = getter()
        if now != _state[key_tp]:
            _state[key_tp] = now
            for listener in _listeners[key_tp]:
                listener(now)


"""
/opt/REAPER/Plugins/reaper_python.py @ 2826

Script execution error

Traceback (most recent call last):
  ...
    retval = RPR_MIDI_GetRecentInputEvent(*tu)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  ...
    return (r,p0,rpr_unpacks(t[1]),int(t[2].value),int(t[3].value),int(t[4].value),float(t[5].value),int(t[6].value))
                 ^^^^^^^^^^^^^^^^^
  File "/opt/REAPER/Plugins/reaper_python.py", line 47, in rpr_unpacks
    return str(v.value.decode())
               ^^^^^^^^^^^^^^^^
UnicodeDecodeError: 'utf-8' codec can't decode byte 0x89 in position 0: invalid start byte
"""


def RPR_MIDI_GetRecentInputEvent(p0,p1,p2,p3,p4,p5,p6):
   #a=_ft['MIDI_GetRecentInputEvent']
   a=rpr_getfp('MIDI_GetRecentInputEvent')
   f=CFUNCTYPE(c_int,c_int,c_char_p,c_void_p,c_void_p,c_void_p,c_void_p,c_void_p)(a)
   t=(c_int(p0),rpr_packs(p1),c_int(p2),c_int(p3),c_int(p4),c_double(p5),c_int(p6))
   r=f(t[0],t[1],byref(t[2]),byref(t[3]),byref(t[4]),byref(t[5]),byref(t[6]))
   # Cannot return t[1].value because it could contain embedded null characters (eg. CC value=0)
   #return (r,p0,rpr_unpacks(t[1]),int(t[2].value),int(t[3].value),int(t[4].value),float(t[5].value),int(t[6].value))
   return (r,p0,_midi_buffer(t[1]),int(t[2].value),int(t[3].value),int(t[4].value),float(t[5].value),int(t[6].value))


def _midi_buffer(buf):
    status = buf.raw[0] & 0xF0
    size = 1

    if status == 0x80 or status == 0x90 or status == 0xB0:
        size = 3  # note off, note on, cc
    if status == 0xC0:
        size = 2  # pc

    return buf.raw[0:size]

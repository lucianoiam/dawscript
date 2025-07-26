# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

import jack
import queue
import os
import signal
import sys
import time
import threading
from types import ModuleType
from typing import Any, Callable, List, Tuple

from ..types import AnyHandle, ParameterHandle, PluginHandle, TrackHandle, TrackType

_controller = None
_jack_client: jack.Client = None
_jack_midi_in: jack.OwnPort = None
_midi_queue = queue.Queue()


def name() -> str:
    return "cli"


def main(controller: ModuleType, context: Any):
    global _controller
    _controller = controller
    _run_loop()


def log(message: str):
    print(message)


def display(message: str):
    print(message)


def get_stable_object_id(handle: AnyHandle) -> str:
    return handle


def get_tracks() -> List[TrackHandle]:
    log(f"stub: get_tracks()")
    return []


def get_track_type(track: TrackHandle) -> TrackType:
    log(f"stub: get_track_type( {track} )")
    return TrackType.AUDIO


def get_track_name(track: TrackHandle) -> str:
    log(f"stub: get_track_name( {track} )")
    return ''


def is_track_mute(track: TrackHandle) -> bool:
    log(f"stub: is_track_mute( {track} )")
    return False


def set_track_mute(track: TrackHandle, mute: bool):
    log(f"stub: set_track_mute( {track} )")


def add_track_mute_listener(track: TrackHandle, listener: Callable[[bool], None]):
    log(f"stub: add_track_mute_listener( {track}, {listener} )")


def remove_track_mute_listener(track: TrackHandle, listener: Callable[[bool], None]):
    log(f"stub: remove_track_mute_listener( {track}, {listener} )")


def get_track_volume(track: TrackHandle) -> float:
    log(f"stub: get_track_volume( {track} )")
    return 0.0


def set_track_volume(track: TrackHandle, volume: float):
    log(f"stub: set_track_volume( {track}, {volume} )")


def add_track_volume_listener(track: TrackHandle, listener: Callable[[float], None]):
    log(f"stub: add_track_volume_listener( {track}, {listener} )")


def remove_track_volume_listener(track: TrackHandle, listener: Callable[[float], None]):
    log(f"stub: remove_track_volume_listener( {track}, {listener} )")


def get_track_pan(track: TrackHandle) -> float:
    log(f"stub: get_track_pan( {track} )")
    return 0.0


def set_track_pan(track: TrackHandle, pan: float):
    log(f"stub: set_track_pan( {track}, {pan} )")


def add_track_pan_listener(track: TrackHandle, listener: Callable[[float], None]):
    log(f"stub: add_track_pan_listener( {track}, {listener} )")


def remove_track_pan_listener(track: TrackHandle, listener: Callable[[float], None]):
    log(f"stub: remove_track_pan_listener( {track}, {listener} )")


def get_track_plugins(track: TrackHandle) -> List[PluginHandle]:
    log(f"stub: get_track_plugins( {track} )")
    return []


def get_plugin_name(plugin: PluginHandle) -> str:
    log(f"stub: get_plugin_name( {plugin} )")
    return ''


def is_plugin_enabled(plugin: PluginHandle) -> bool:
    log(f"stub: is_plugin_enabled( {plugin} )")
    return False


def set_plugin_enabled(plugin: PluginHandle, enabled: bool):
    log(f"stub: set_plugin_enabled( {plugin}, {enabled} )")


def add_plugin_enabled_listener(plugin: PluginHandle, listener: Callable[[bool], None]):
    log(f"stub: add_plugin_enabled_listener( {plugin}, {listener} )")


def remove_plugin_enabled_listener(plugin: PluginHandle, listener: Callable[[bool], None]):
    log(f"stub: remove_plugin_enabled_listener( {plugin}, {listener} )")


def get_plugin_parameters(plugin: PluginHandle) -> List[ParameterHandle]:
    log(f"stub: get_plugin_parameters( {plugin} )")
    return []


def get_parameter_name(param: ParameterHandle) -> str:
    log(f"stub: get_parameter_name( {param} )")
    return ''


def get_parameter_range(param: ParameterHandle) -> Tuple[float, float]:
    log(f"stub: get_parameter_range( {param} )")
    return (0, 1.0)


def get_parameter_value(param: ParameterHandle) -> float:
    log(f"stub: get_parameter_value( {param} )")
    return 0.0


def set_parameter_value(param: ParameterHandle, value: float):
    log(f"stub: set_parameter_value( {param}, {value} )")


def add_parameter_value_listener(
    param: ParameterHandle, listener: Callable[[float], None]
):
    log(f"stub: add_parameter_value_listener( {param}, {listener} )")


def remove_parameter_value_listener(
    param: ParameterHandle, listener: Callable[[float], None]
):
    log(f"stub: remove_parameter_value_listener( {param}, {listener} )")


def _run_loop():
    global _jack_client, _jack_midi_in

    ev_port_reg = threading.Event()
    ev_quit = threading.Event()

    try:
        _jack_client = jack.Client(
            f"dawscript_{os.urandom(2).hex()}", no_start_server=True
        )
    except jack.JackOpenError:
        sys.exit(1)

    _jack_midi_in = _jack_client.midi_inports.register(f"input")
    _jack_client.set_process_callback(_jack_proc)
    _jack_client.set_port_registration_callback(lambda p, r: ev_port_reg.set())
    _jack_client.activate()

    signal.signal(signal.SIGINT, lambda sig, frame: ev_quit.set())

    try:
        _controller.on_script_start()
    except AttributeError:
        pass

    while not ev_quit.is_set():
        if ev_port_reg.is_set():
            ev_port_reg.clear()
            _connect_ports()
        _controller.host_callback(_read_midi_events())
        time.sleep(1 / 30)

    _jack_client.deactivate()
    _jack_client.close()


def _jack_proc(frames: int):
    for offset, data in _jack_midi_in.incoming_midi_events():
        _midi_queue.put_nowait(bytes(data))


def _connect_ports():
    try:
        config = _controller.get_config()
    except AttributeError:
        config = None
        print("config not available", file=sys.stderr)

    np = "|".join(config.midi_inputs) if config and isinstance(config.midi_inputs, list) else ''
    midi_inputs = _jack_client.get_ports(name_pattern=np, is_midi=True, is_output=True)

    for some_midi_input in midi_inputs:
        try:
            if not _jack_midi_in.is_connected_to(some_midi_input):
                _jack_midi_in.connect(some_midi_input)
                log(f"{some_midi_input.name} <- {_jack_midi_in.name}")
        except jack.JackError as e:
            print(str(e), file=sys.stderr)


def _read_midi_events():
    events = list()

    while _midi_queue.qsize() > 0:
        events.append(_midi_queue.get_nowait())

    return events

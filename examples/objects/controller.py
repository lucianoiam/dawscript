# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

from typing import List

from dawscript_core.host import ALL_MIDI_INPUTS, Config, TrackNotFoundError
from dawscript_core.extra.gadget import Footswitch
from dawscript_core.extra.objects import Host, Track

config = Config(midi_inputs=ALL_MIDI_INPUTS)

footswitch = Footswitch()
footswitch.map_midi_press(type="control_change", control=64, value=127, omni=True)
footswitch.map_midi_release(type="control_change", control=64, value=0, omni=True)


def on_project_load():
    try:
        callback = Track("Track 1").toggle_mute
        footswitch.set_callback_pressed(callback)
        # callback = Track('...').plugin('Reverb').toggle_enabled
        # footswitch.set_callback_pressed_twice(...)
        # footswitch.set_callback_released(...)
        # footswitch.set_callback_released_slow(...)
    except TrackNotFoundError:
        Host.display("Incompatible project loaded")


def host_callback(midi: List[bytes]):
    footswitch.process(midi)

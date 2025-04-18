# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

from typing import List

from dawscript_core.host import ALL_MIDI_INPUTS, Config, get_track_by_name, toggle_track_mute
from dawscript_core.util import make_midi_messages
from dawscript_core.extra.gadget import Footswitch

footswitch = Footswitch()


def get_config() -> Config:
    return Config(midi_inputs=ALL_MIDI_INPUTS)


def host_callback(midi: List[bytes]):
    for msg in make_midi_messages(midi):
        if msg.is_cc() and msg.control == 64:
            if msg.value == 127:
                footswitch.press()
            elif msg.value == 0:
                footswitch.release()

    if footswitch.poll():
        if footswitch.pressed():
            toggle_track_mute(get_track_by_name("Track 1"))
        # elif footswitch.pressed_twice():
        #   toggle_plugin_enabled(get_track_plugin_by_name(get_track_by_name('...'), 'Reverb'))
        # elif footswitch.released():
        #   ...
        # elif footswitch.released_slow():
        #   ...

# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

from gadget import Footswitch, make_midi_messages
from host import ALL_MIDI_INPUTS, Config, get_track, toggle_track_mute

config = Config(midi_inputs=ALL_MIDI_INPUTS)

footswitch = Footswitch()

def host_callback(midi: list[bytes]):
   for msg in make_midi_messages(midi):
      if msg.is_cc() and msg.control == 64:
         if msg.value == 127:
            footswitch.press()
         elif msg.value == 0:
            footswitch.release()

   if footswitch.poll():
      if footswitch.pressed():
         toggle_track_mute(get_track('Track 1'))
      #elif footswitch.pressed_twice():
      #   toggle_plugin_enabled(get_plugin(get_track('...'), 'Reverb'))
      #elif footswitch.released():
      #   ...
      #elif footswitch.released_slow():
      #   ...

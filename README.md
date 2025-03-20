DAWScript
=========
This project provides an abstraction layer for a minimal subset of the scripting
APIs found in some popular DAWs (Digital Audio Workstations), with a focus on
mixer control.

In its current form, it is useful as a programmable MIDI-learn-like tool that
requires little to no coding skills.

Goals
-----
- Control mixer and plugin parameters
- Run the same unmodified code on different DAWs. Currently, REAPER and Ableton
Live 11+ are supported.
- Handle all the boilerplate
- Be easy to use for casual users
- Be self-explanatory to programmers

Current Features
----------------
- MIDI input
- Track volume, panning, and mute control
- Plugin bypass and parameter control
- Listeners
- Footswitch logic with gestures like press, double press, and long press

Features Under Development
--------------------------
- Network bridge to JavaScript running on a browser

Requirements
------------
- Python 3
- REAPER users need to set it up manually
- Live 11+ already comes with an embedded interpreter

Quick Start
-----------
Copy or symlink one of the controller.py files in the `examples` directory to
the project's root directory (where dawscript.py resides). How to install the
script depends on the DAW, detailed instructions coming soon.

Examples
--------
All the examples are functionally equivalent but differ in implementation. The
mute state of a track named *Track 1* is toggled when a footswitch that sends
MIDI control messages for *Sustain Pedal* (CC64) is pressed:

[No-code setup using a configuration file](https://github.com/lucianoiam/dawscript/blob/master/examples/config_file/config.yml)
```yaml
# config_file.yml

- footswitch:
    midi:
      press: control_change 64 127
      release: control_change 64 0
    gestures:
      pressed: host.toggle_track_mute_by_name, Track 1
```
```python
# controller.py

(config, gadgets) = parse_config_file(
   dawscript_relpath(os.path.join('examples', 'config_file', 'config.yml')),
   globals()
)

def host_callback(midi: List[bytes]):
   for gadget in gadgets:
      gadget.process(midi)
```

[Object-oriented tracks API](https://github.com/lucianoiam/dawscript/blob/master/examples/high_level_api/controller.py)
```python
# controller.py

config = Config(midi_inputs=ALL_MIDI_INPUTS)

footswitch = Footswitch()
footswitch.map_midi_press(type='control_change',control=64, value=127, omni=True)
footswitch.map_midi_release(type='control_change', control=64, value=0, omni=True)

def on_project_load():
   try:
      callback = Track('Track 1').toggle_mute
      footswitch.set_callback_pressed(callback)
   except TrackNotFoundError:
      Host.log('Incompatible project loaded')

def host_callback(midi: List[bytes]):
   footswitch.process(midi)
```

[Plain calls to DAW abstraction interface](https://github.com/lucianoiam/dawscript/blob/master/examples/low_level_api/controller.py)
```python
# controller.py

config = Config(midi_inputs=ALL_MIDI_INPUTS)
footswitch = Footswitch()

def host_callback(midi: List[bytes]):
   for msg in make_midi_messages(midi):
      if msg.is_cc() and msg.control == 64:
         if msg.value == 127:
            footswitch.press()
         elif msg.value == 0:
            footswitch.release()

   if footswitch.poll():
      if footswitch.pressed():
         host.toggle_track_mute(host.get_track('Track 1'))
```

How to Install
--------------
*Coming soon*

Debug Environment
-----------------
Debugging while running on a DAW can be a tedious process, so DAWScript can also
run stand-alone when started from a terminal. In this case, a JACK server is
required to provide MIDI input, and calls to the DAW APIs target a mock
implementation that prints to stdout. MIDI implementation is planned to be
replaced by RtMidi so no additional software is required.

Related Tools
-------------
Check out [Consul](https://github.com/lucianoiam/consul), my CLAP/VST plugin
for MIDI remote control.

Useful Links
------------
REAPER \
https://www.reaper.fm/sdk/reascript/reascripthelp.html \
https://forums.cockos.com/showthread.php?p=2572493 \
https://github.com/majek/wdl/blob/master/WDL/db2val.h

Live \
https://nsuspray.github.io/Live_API_Doc/11.0.0.xml \
https://github.com/gluon/AbletonLive11_MIDIRemoteScripts

Other \
https://jackclient-python.readthedocs.io/en/0.5.5/ \
https://mido.readthedocs.io/en/stable/ \
https://www.standardsapplied.com/nonlinear-curve-fitting-calculator.html


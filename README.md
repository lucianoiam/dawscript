dawscript
=========
This project provides an abstraction layer for a small subset of the scripting
APIs found in some DAWs (Digital Audio Workstations).

Goals
-----
- Control mixer and plugin parameters
- Create networked user interfaces
- Run the same unmodified code across different DAWs

Current Features
----------------
- Compatibility with REAPER, Ableton Live 11+ and Bitwig Studio.
- Track volume, panning, and mute control
- Plugin bypass and parameter control
- MIDI input
- Listeners
- Network bridge to JavaScript running on a browser

Requirements
------------
- Python 3 DLL for REAPER users
- Standalone Python 3 executable for Bitwig users
- Live 11+ already comes with an embedded Python 3 interpreter

Quick Start
-----------
Copy or symlink one of the controller.py files in the `examples` directory to
the project's root directory (where README.md resides). The script entry point
is defined in dawscript.py. How to install the script depends on the DAW,
detailed instructions coming soon.

Examples
--------
All examples except «web» are functionally equivalent but differ in
implementation. The mute state of a track named *Track 1* is toggled when a
footswitch that sends MIDI control messages for *Sustain Pedal* (CC64)
is pressed:

[Calls to raw DAW abstraction interface](https://github.com/lucianoiam/dawscript/blob/master/examples/raw/controller.py)
```python
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
         host.toggle_track_mute(host.get_track_by_name('Track 1'))
```

[Object-oriented API](https://github.com/lucianoiam/dawscript/blob/master/examples/objects/controller.py)
```python
footswitch = Footswitch()
footswitch.map_midi_press(type='control_change',control=64, value=127, omni=True)
footswitch.map_midi_release(type='control_change', control=64, value=0, omni=True)

def get_config() -> Config:
   return Config(midi_inputs=ALL_MIDI_INPUTS)

def on_project_load():
   try:
      callback = Track('Track 1').toggle_mute
      footswitch.set_callback_pressed(callback)
   except TrackNotFoundError:
      Host.display('Incompatible project loaded')

def host_callback(midi: List[bytes]):
   footswitch.process(midi)
```

[No-code setup using a configuration file](https://github.com/lucianoiam/dawscript/blob/master/examples/config_file/config.yml)
```yaml
- footswitch:
    midi:
      press: control_change 64 127
      release: control_change 64 0
    gestures:
      pressed: host.toggle_track_mute_by_name, Track 1
```
```python
config, gadgets = parse_config_file('config.yml', globals())

def get_config() -> Config:
   return config

def host_callback(midi: List[bytes]):
   for gadget in gadgets:
      gadget.process(midi)
```

[Control track volume from a web browser](https://github.com/lucianoiam/dawscript/blob/master/examples/web/htdocs/example.js)
```javascript
const { host, connect } = dawscript;

const track = await host.getTrack('Track 1');

const slider = document.createElement('input');
slider.type = 'range';
slider.min = 0;
slider.max = 1.0;
slider.step = 0.001;
slider.value = await host.getTrackVolume(track);

slider.addEventListener('input', (ev) => {
   host.setTrackVolume(track, parseFloat(slider.value));
});

host.addTrackVolumeListener(track, (vol) => {
   slider.value = vol;
});

connect();
```

The web client is advertised using DNS-SD (Bonjour) under the name «dawscript»,
for easy access using discovery apps like these on [iOS](https://apps.apple.com/app/abc-bonjour/id1172137819)
or [Android](https://play.google.com/store/apps/details?id=de.wellenvogel.bonjourbrowser).

Current Limitations
-------------------
- MIDI output is not implemented
- MIDI events are only available to the locally running Python script

How to Install
--------------
*Coming soon*

Debug Environment
-----------------
Debugging while running on a DAW can be a tedious process, so dawscript can also
run stand-alone when started from a terminal. In this case a JACK server is
required to provide MIDI input, and calls to the DAW APIs target a mock
implementation that prints to stdout. MIDI implementation is planned to be
replaced by RtMidi so no additional software is required.

The example `console` implements a [RPyC](https://github.com/tomerfiliba-org/rpyc)
REPL console that connects to the host from a script running on a separate
process, for example started from a terminal.

Related Tools
-------------
- [LAN Mixer](https://github.com/lucianoiam/lanmixer), dawscript-based mixer and
plugin control over the network. Early stage project.
- [Consul](https://github.com/lucianoiam/consul), CLAP/VST plugin for MIDI remote
control.
- [Guinda](https://github.com/lucianoiam/guinda), a single file library of Web
Components for audio applications.

Useful Links
------------
REAPER \
https://www.reaper.fm/sdk/reascript/reascripthelp.html \
https://forums.cockos.com/showthread.php?p=2572493 \
https://github.com/majek/wdl/blob/master/WDL/db2val.h

Live \
https://nsuspray.github.io/Live_API_Doc/11.0.0.xml \
https://github.com/gluon/AbletonLive11_MIDIRemoteScripts

Bitwig \
https://mvnrepository.com/artifact/com.bitwig/extension-api/22 \
https://www.py4j.org/

Other \
https://jackclient-python.readthedocs.io/en/0.5.5/ \
https://mido.readthedocs.io/en/stable/ \
https://www.standardsapplied.com/nonlinear-curve-fitting-calculator.html

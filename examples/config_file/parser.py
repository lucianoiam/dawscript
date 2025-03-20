# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

from collections import namedtuple
from typing import Callable, List

import yaml
from mido import Message

from gadget import Footswitch
from host import Config, host

ParsedGadget = namedtuple('ParsedGadget', ['instance', 'name', 'midi_port'])

def parse_config_file(yml_file: str, ctrl_globals: dict) -> (Config,list):
   gadgets = _make_gadgets(yml_file, ctrl_globals)
   return (_make_config(gadgets), [g.instance for g in gadgets])

def _make_gadgets(yml_file: str, ctrl_globals: dict) -> list[ParsedGadget]:
   gadgets = list()

   for config_dict in yaml.load(open(yml_file, 'r'), Loader=yaml.Loader):
      type = next(iter(config_dict))
      config = config_dict[type]
      gadgets.append(ParsedGadget(
         instance=_make_gadget(type, config, ctrl_globals),
         name=config.get('name'),
         midi_port=config['midi'].get('port', None)
      ))

   return gadgets

def _make_gadget(type: str, config: dict, ctrl_globals: dict):
   if type == 'footswitch':
      return _make_footswitch(config, ctrl_globals)
   else:
      raise Exception(f'Gadget type not supported: {type}')

def _make_footswitch(config: dict, ctrl_globals: dict) -> Footswitch:
   instance = Footswitch()
   channel = config['midi'].get('channel', 'omni')
   omni = channel == 'omni'
   if omni:
      channel = 1

   msg = _make_message(config['midi']['press'], ch_from_1=channel)
   instance.map_midi_press(msg, omni)
   msg = _make_message(config['midi']['release'], ch_from_1=channel)
   instance.map_midi_release(msg, omni)

   for state, pseudocode in config['gestures'].items():
      set_callback = getattr(instance, f'set_callback_{state}')
      set_callback(_build_callback(pseudocode, ctrl_globals))

   return instance

def _make_message(serialized_msg: str, ch_from_1: int = 1) -> Message:
   (status, *sdata) = serialized_msg.split(' ')
   idata = [int(s) for s in sdata]
   channel = ch_from_1 - 1
   if status == 'control_change':
      return Message(status, channel=channel, control=idata[0], value=idata[1])
   elif status == 'note_on':
      return Message(status, channel=channel, note=idata[0])
   elif status == 'note_off':
      return Message(status, channel=channel, note=idata[0])
   else:
      raise Exception(f'Message type not supported: {status}')

def _make_config(gadgets: List[ParsedGadget]):
   return Config(midi_inputs=set([g.midi_port for g in gadgets if g.midi_port]))

def _build_callback(pseudocode: str, ctrl_globals: dict):
   (expr, *args) = map(str.strip, pseudocode.split(','))
   for i in range(0, len(args)):
      try:
         args[i] = str(float(args[i]))
      except ValueError:
         args[i] = '\'' + args[i].replace('\'', '\\\'') + '\''
   expr += '(' + ','.join(args) + ')'
   return lambda: exec(compile(expr, '', 'exec'), ctrl_globals)

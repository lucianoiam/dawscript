# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

from gadget import make_config_and_gadgets, process_midi
from host import dawscript_relpath
#from example_functions import pressed_twice_callback

(config, gadgets) = make_config_and_gadgets(
   dawscript_relpath('examples/config_file/config.yml'),
   globals()
)

def host_callback(midi: list[bytes]):
   process_midi(midi, gadgets)

# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

import gadget
import host
#from example_functions import pressed_twice_callback

(config, gadgets) = gadget.make_from_yaml(
   host.dawscript_relpath('examples/config_file.yml'),
   globals()
)

def host_callback(midi: list[bytes]):
   gadget.process_midi(midi, gadgets)

def on_project_load():
   pass

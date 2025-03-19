# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

from typing import List

from host import dawscript_relpath
from examples.config_file.parser import parse_config_file
#from example_functions import pressed_twice_callback

(config, gadgets) = parse_config_file(
   dawscript_relpath('examples/config_file/config.yml'),
   globals()
)

def host_callback(midi: List[bytes]):
   for gadget in gadgets:
      gadget.process(midi)

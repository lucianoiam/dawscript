# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

import os
import sys
from typing import List

from host import dawscript_relpath

proj_path = dawscript_relpath(os.path.join('examples', 'config_file'))
sys.path.insert(0, os.path.join(proj_path, 'site-packages'))
from examples.config_file.parser import parse_config_file

#from example_functions import pressed_twice_callback

(config, gadgets) = parse_config_file(
   os.path.join(proj_path, 'config.yml'),
   globals()
)

def host_callback(midi: List[bytes]):
   for gadget in gadgets:
      gadget.process(midi)

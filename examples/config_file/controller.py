# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

import os
import sys
from typing import List

from util import add_site_packages, dawscript_path

ds_path = dawscript_path('examples', 'config_file')
add_site_packages(ds_path)

from examples.config_file.parser import parse_config_file

#from example_functions import pressed_twice_callback

(config, gadgets) = parse_config_file(
   os.path.join(ds_path, 'config.yml'),
   globals()
)

def host_callback(midi: List[bytes]):
   for gadget in gadgets:
      gadget.process(midi)

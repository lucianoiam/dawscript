# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

import os
import sys
from typing import List

from extra.config_file import parse_config_file
from util import dawscript_path

# from example_functions import pressed_twice_callback

(config, gadgets) = parse_config_file(
    dawscript_path("examples", "config_file", "config.yml"), globals()
)


def host_callback(midi: List[bytes]):
    for gadget in gadgets:
        gadget.process(midi)

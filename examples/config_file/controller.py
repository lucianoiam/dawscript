# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

from typing import List

from dawscript_core.host import Config
from dawscript_core.util import dawscript_path
from dawscript_core.extra.config_file import parse_config_file

# from example_functions import pressed_twice_callback

config, gadgets = parse_config_file(
    dawscript_path("examples", "config_file", "config.yml"),
    globals()
)


def get_config() -> Config:
    return config


def host_callback(midi: List[bytes]):
    for gadget in gadgets:
        gadget.process(midi)

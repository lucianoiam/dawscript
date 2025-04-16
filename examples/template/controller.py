# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

from typing import List

from dawscript_core.host import ALL_MIDI_INPUTS, Config


def get_config() -> Config:
    return Config(midi_inputs=ALL_MIDI_INPUTS)


def on_script_start():
    pass


def on_script_stop():
    pass


def on_project_load():
    pass


def host_callback(midi: List[bytes]):
    pass

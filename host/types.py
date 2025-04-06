# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

from collections import namedtuple
from typing import Any

ALL_MIDI_INPUTS = []

Config = namedtuple("Config", ["midi_inputs"])

TrackHandle = Any
PluginHandle = Any
ParameterHandle = Any


class TrackNotFoundError(Exception):
    def __init__(self, name: str):
        super().__init__(f'Track with name "{name}" does not exist')


class PluginNotFoundError(Exception):
    def __init__(self, name: str):
        super().__init__(f'Plugin with name "{name}" does not exist')


class ParameterNotFoundError(Exception):
    def __init__(self, name: str):
        super().__init__(f'Parameter with name "{name}" does not exist')


class IncompatibleEnvironmentError(Exception):
    pass

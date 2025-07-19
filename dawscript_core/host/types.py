# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

from collections import namedtuple
from enum import Enum
from typing import Any

ALL_MIDI_INPUTS = None

Config = namedtuple("Config", ["midi_inputs"])

AnyHandle = Any
TrackHandle = Any
PluginHandle = Any
ParameterHandle = Any


class TrackType(Enum):
    AUDIO = 0
    MIDI = 1
    OTHER = 2


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

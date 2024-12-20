# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

from .factory import *
from .footswitch import *
from .midoutil import *
from .types import Gadget

def process_midi(midi: list[bytes], gadgets: list[Gadget]):
   for gadget in gadgets:
      gadget.process(midi)

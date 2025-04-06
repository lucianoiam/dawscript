# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

# This __init__.py file is only needed by Ableton Live

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from .host.live import DawscriptControlSurface


def create_instance(c_instance):
    return DawscriptControlSurface(c_instance)

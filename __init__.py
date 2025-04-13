#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

import os
import sys

try:
    from dawscript_core.host import main
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    from dawscript_core.host import DawscriptControlSurface, main

from dawscript_core.util import dawscript_path


# Uncomment when adding dawscript as a git submodule
# __file__ is not defined for __init__.py on REAPER
#alt_controller_path = dawscript_path("..")


def import_controller():
    try:
        sys.path.insert(0, alt_controller_path)
    except NameError:
        pass

    import controller

    try:
        if sys.path[0] == alt_controller_path:
            del sys.path[0]
    except NameError:
        pass

    return controller


# Entry point for Ableton Live
def create_instance(c_instance):
    instance = DawscriptControlSurface(c_instance)
    main(import_controller(), instance)

    return instance


# Entry point for REAPER and CLI
if __name__ == "__main__":
    main(import_controller(), globals())

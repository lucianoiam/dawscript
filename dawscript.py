#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

import os
import sys

try:
    from dawscript_core.host import main
except ModuleNotFoundError:
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    from dawscript_core.host import DawscriptControlSurface, main

import controller

#from dawscript_core.extra.web import controller
#controller.set_config( ... )


# Entry point for Ableton Live
def create_instance(c_instance):
    instance = DawscriptControlSurface(c_instance)
    main(controller, instance)

    return instance


# Entry point for REAPER and CLI
if __name__ == "__main__":
    main(controller, globals())

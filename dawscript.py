#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

import os
import sys


# Edit as necessary
def load_controller():
    # Your own controller implementation
    import controller

    # Default controller for web scripts
    #from dawscript_core.extra.web import controller
    #controller.set_server_config( ... )

    return controller


# Entry point for Ableton Live
def create_instance(c_instance):
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    from dawscript_core.host import DawscriptControlSurface, main

    instance = DawscriptControlSurface(c_instance)
    main(load_controller(), instance)

    return instance


# Entry point for REAPER, Bitwig and CLI
if __name__ == "__main__":
    from dawscript_core.host import main

    main(load_controller(), globals())

#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

import os
import sys


# Entry point for Ableton Live
def create_instance(c_instance):
    sys.path.insert(0, os.path.dirname(__file__))
    from dawscript.host import DawscriptControlSurface, main

    instance = DawscriptControlSurface(c_instance)
    main(instance)

    return instance


# Entry point for REAPER and CLI
if __name__ == "__main__":
    from dawscript.host import main

    main(globals())

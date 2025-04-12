# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

import importlib
import os
import sys


def load_controller():
    try:
        return import_controller()
    except ModuleNotFoundError:
        git_root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

        try:
            sys.path.insert(0, git_root_path)
            return import_controller()
        finally:
            if sys.path[0] == git_root_path:
                del sys.path[0]


def import_controller():
    return importlib.import_module("controller")

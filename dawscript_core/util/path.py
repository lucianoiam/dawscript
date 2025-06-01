# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

import os
import sys


def add_site_packages(caller_path):
    caller_dir = os.path.dirname(os.path.realpath(caller_path))
    pkg_path = os.path.join(caller_dir, "site-packages")
    sys.path.insert(0, pkg_path)


def dawscript_path(*args) -> str:
    this_source_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.abspath(os.path.join(this_source_dir, "..", '..', *args))

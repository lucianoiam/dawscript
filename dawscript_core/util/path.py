# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

import os
import sys


def add_site_packages(caller_path):
    pkg_path = os.path.join(os.path.dirname(caller_path), "site-packages")
    sys.path.insert(0, pkg_path)


def dawscript_path(*args) -> str:
    this_source_path = os.path.dirname(os.path.realpath(__file__))
    return os.path.abspath(os.path.join(this_source_path, "..", '..', *args))

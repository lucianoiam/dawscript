# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

import os
import sys


def add_site_packages(*args):
    ds_path = dawscript_path()

    if len(args) == 0:
        pkg_path = os.path.join(ds_path, "site-packages")
    elif len(args) == 1 and args[0].startswith(ds_path):
        pkg_path = os.path.join(args[0], "site-packages")
    else:
        pkg_path = dawscript_path(*args, "site-packages")

    sys.path.insert(0, pkg_path)


def dawscript_path(*args) -> str:
    this_source_path = os.path.dirname(os.path.realpath(__file__))
    return os.path.abspath(os.path.join(this_source_path, "..", *args))

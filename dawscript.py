#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

# __file__ is not defined for dawscript.py on REAPER

from typing import Any

from util import add_site_packages
import host

add_site_packages()

def main(context: Any):
   host.set_context(context)
   host.run_loop()

if __name__ == '__main__':
   main(globals())

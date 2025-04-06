#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

# __file__ is not defined for dawscript.py on REAPER

from typing import Any

import host


def main(context: Any):
    host.main(context)


if __name__ == "__main__":
    main(globals())

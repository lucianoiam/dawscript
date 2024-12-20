#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

from typing import Any

import host

def main(context: Any):
   host.set_context(context)
   host.run_loop()

if __name__ == '__main__':
   main(globals())

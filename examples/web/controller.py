# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

from typing import List

from extra.web import server
from util import dawscript_path

HTDOCS = dawscript_path('examples', 'web', 'htdocs')

def on_script_start():
   server.start(HTDOCS)

def on_script_stop():
   server.stop()

def host_callback(midi: List[bytes]):
   server.do_work()

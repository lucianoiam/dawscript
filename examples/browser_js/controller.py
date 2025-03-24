# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

from typing import List

from util import add_site_packages
add_site_packages('examples', 'browser_js')

from examples.browser_js import server

def on_script_start():
   server.start()

def on_script_stop():
   server.stop()

def host_callback(midi: List[bytes]):
   server.do_work()

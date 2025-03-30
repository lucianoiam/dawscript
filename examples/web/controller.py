# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

from typing import List

import host
from extra.web import server
from util import dawscript_path

def on_script_start():
   htdocs_path = dawscript_path('examples', 'web', 'htdocs')
   urls = server.start(htdocs_path, service_name='dawscript')

   for url in urls:
      host.log(f'dawscript @ {url}')

def on_script_stop():
   server.stop()

def host_callback(midi: List[bytes]):
   server.do_work()

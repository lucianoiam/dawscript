# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

from typing import List

from dawscript_core import host
from dawscript_core.extra.web import server


_htdocs_path = None
_display_messages = None
_kwargs = {}


def set_server_config(htdocs_path, display_messages=True, **kwargs):
   global _htdocs_path, _display_messages, _kwargs
   _htdocs_path = htdocs_path
   _display_messages = display_messages
   _kwargs = kwargs


def on_script_start():
    try:
        urls = server.start(_htdocs_path, **_kwargs)
        for url in urls:
            _display_message(f"@ {url}")
    except Exception as e:
        _display_message(f"error: {e}")


def on_script_stop():
    server.stop()


def host_callback(midi: List[bytes]):
    server.tick()


def _display_message(message):
    if _display_messages:
        service_name = _kwargs.get("service_name", "dawscript")
        host.display(f"{service_name} {message}")

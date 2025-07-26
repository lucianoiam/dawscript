# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

from typing import List

from dawscript_core import host
from dawscript_core.extra.web import server


_display_messages = None
_args = []
_kwargs = {}



def set_server_config(*args, display_messages=True, **kwargs):
	global _display_messages, _args, _kwargs
	_display_messages = display_messages
	_args = args
	_kwargs = kwargs


def display(message):
	if _display_messages:
		host.display(message)


def on_script_start():
    service_name = _kwargs.get("service_name", "dawscript");
    try:
        urls = server.start(*_args, **_kwargs)
        for url in urls:
            display(f"{service_name} @ {url}")
    except Exception as e:
        display(f"{service_name} error: {e}")


def on_script_stop():
    server.stop()


def host_callback(midi: List[bytes]):
    server.tick()

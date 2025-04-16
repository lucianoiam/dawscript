# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

from typing import List

from dawscript_core import host
from dawscript_core.extra.web import server


_htdocs_path = None
_ws_port = None
_http_port = None
_service_name = None
_display_messges = None


def set_server_config(htdocs_path, ws_port=49152, http_port=8080,
	service_name=None, display_messges=True):

	global _htdocs_path, _ws_port, _http_port, _service_name, _display_messges
	_htdocs_path = htdocs_path
	_ws_port = ws_port
	_http_port = http_port
	_service_name = service_name
	_display_messges = display_messges


def display(message):
	if _display_messges:
		host.display(message)


def on_script_start():
    try:
        urls = server.start(_htdocs_path, _ws_port, _http_port,
        	service_name=_service_name)

        for url in urls:
            display(f"{_service_name} @ {url}")
    except Exception as e:
        display(f"{_service_name} error: {e}")


def on_script_stop():
    server.stop()


def host_callback(midi: List[bytes]):
    server.tick()

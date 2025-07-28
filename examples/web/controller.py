# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

from dawscript_core.util import dawscript_path
from dawscript_core.extra.web import controller


HTDOCS = ["examples", "web"]
SERVICE_NAME = "dawscript"

controller.set_server_config(dawscript_path(*HTDOCS), service_name=SERVICE_NAME)

on_script_start = controller.on_script_start
on_script_stop = controller.on_script_stop
host_callback = controller.host_callback

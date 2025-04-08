# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

import os
import subprocess

proc: subprocess.Popen = None


def register_service(name, service_type, port, address):
    global proc
    
    if _is_command_in_path("dns-sd"):
        proc = subprocess.Popen(
            ["dns-sd", "-R", name, service_type, ".", str(port), address]
        )
    elif _is_command_in_path("avahi-publish"):
        proc = subprocess.Popen(
            ["avahi-publish", "-s", name, service_type, str(port), address]
        )
    else:
        raise RuntimeError("dns-sd unavailable")


def unregister_service():
    if proc is not None:
        proc.terminate()
        proc.wait()


def _is_command_in_path(command):
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    extensions = [".exe"] if os.name == "nt" else [""]

    for directory in path_dirs:
        for ext in extensions:
            full_path = os.path.join(directory, command + ext)

            if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                return True

    return False

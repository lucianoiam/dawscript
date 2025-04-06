# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

import os
import socket
import subprocess

zc_instance = None
serv_info = None
subproc: subprocess.Popen = None

try:
    from zeroconf import ServiceInfo, Zeroconf

    zc_instance = Zeroconf()
except BaseException:
    """
    # The zeroconf module is not available on Live because its built-in Python
    # interpreter lacks support for ctypes, which is required by ifaddr.
    """
    pass


def register_service(name, service_type, port, address):
    address_str = socket.inet_ntoa(address)

    if zc_instance is not None:
        global serv_info
        serv_info = ServiceInfo(
            f"{service_type}.local.",
            f"{name}.{service_type}.local.",
            addresses=[address],
            port=port,
        )
        zc_instance.register_service(serv_info)
    else:
        global subproc
        if _is_command_in_path("dns-sd"):
            subproc = subprocess.Popen(
                ["dns-sd", "-R", name, service_type, ".", str(port), address_str]
            )
        elif _is_command_in_path("avahi-publish"):
            subproc = subprocess.Popen(
                ["avahi-publish", "-s", name, service_type, str(port), address_str]
            )
        else:
            raise RuntimeError("dns-sd unavailable")


def unregister_service():
    if zc_instance is not None:
        zc_instance.unregister_service(serv_info)
        zc_instance.close()
    elif subproc is not None:
        subproc.terminate()
        subproc.wait()


def _is_command_in_path(command):
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    extensions = [".exe"] if os.name == "nt" else [""]

    for directory in path_dirs:
        for ext in extensions:
            full_path = os.path.join(directory, command + ext)

            if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                return True

    return False

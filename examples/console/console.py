#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

import threading
import code
import rpyc


def client_serve(conn, stop):
    while not stop.is_set():
        conn.serve(timeout=0.1)


def main():
    conn = rpyc.classic.connect("localhost", 18861)
    host = conn.modules.dawscript_core.host

    stop = threading.Event()
    thread = threading.Thread(target=client_serve, args=(conn, stop), daemon=True)
    thread.start()

    banner = (
        "\ndawscript REPL Console\n"
        "Imported module `host`\n"
        "Type Ctrl+D or exit() to quit.\n"
    )
    
    try:
         DawscriptConsole(host).interact(banner=banner)
    finally:
        stop.set()
        thread.join()
        conn.close()


class DawscriptConsole(code.InteractiveConsole):
    def __init__(self, host):
        super().__init__(locals={'host': host})
        host_name = host.name()
        self.primary_prompt = f"{host_name}>>> "
        self.secondary_prompt = f"{host_name}... "

    def raw_input(self, prompt=">>> "):
        if prompt.strip() == ">>>":
            return input(self.primary_prompt)
        elif prompt.strip() == "...":
            return input(self.secondary_prompt)
        else:
            return input(prompt)


if __name__ == "__main__":
    main()

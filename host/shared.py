# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

import importlib

from .types import ControllerLoadError

def load_controller():
   nfe = None
   try:
      return importlib.import_module('controller')
   except ModuleNotFoundError as e:
      nfe = e
   if nfe:
      raise ControllerLoadError(nfe)

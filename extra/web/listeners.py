# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

from typing import Callable, Dict, List, Tuple

# ( target_and_setter : [ (client, listener) ] )
_listeners: Dict[str,List[Tuple[str,Callable]]] = {}

def set(client, listener, target, setter):
   key = f'{target}_{setter}'

   if not key in _listeners:
      _listeners[key] = []
      setter(target, lambda v: _call(key, v))

   _listeners[key].append((client, listener))

def remove(client):
   for key in _listeners.keys():
      _listeners[key] = [(c, _) for (c, _) in _listeners[key] if c is not client]

def _call(key, value):
   for (client, listener) in _listeners[key]:
      listener(value)

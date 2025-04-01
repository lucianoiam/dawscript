# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

from typing import Callable, Dict, List, Set, Tuple

import host

# ( target_and_setter : [ (client, name, listener) ] )
_listeners: Dict[str,List[Tuple[str,str,Callable]]] = dict()
_locks: Set[Tuple[str,str]] = set()

def add(client, name, listener, target, setter):
   key = f'{target}_{setter}'

   if not key in _listeners:
      _listeners[key] = []
      try:
         setter(target, lambda v: _call(key, v))
      except Exception as e:
         host.log(e)

   _listeners[key].append((client, name, listener))

def remove(client):
   for key in _listeners.keys():
      _listeners[key] = [(c, _, _) for (c, _, _) in _listeners[key] if c is not client]
   for (c, n) in list(_locks):
      if c is client:
         _locks.remove((c, n))

def skip_next_call(client, name):
   _locks.add((client, name))

def _call(key, value):
   for (client, name, listener) in _listeners[key]:
      lock = (client, name)
      if lock in _locks:
         _locks.remove(lock)
      else:
         listener(value)

# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

import time
from enum import Enum
from typing import Callable, Dict, List, Union

from mido import Message
from dawscript_core.util import is_note_on_or_note_off


class State(Enum):
    PRESSED = 0
    PRESSED_TWICE = 3
    RELEASED = 1
    RELEASED_SLOW = 2


class Footswitch:
    PRESS_TWICE_SEC = 0.3
    RELEASE_SLOW_SEC = 1

    def __init__(self):
        self._state: State = None
        self._midi_map: List[(Message, bool, bool)] = list()
        self._callbacks: Dict[State, Callable] = dict()
        self._release_flag = 0
        self._press_flag = False
        self._press_t = 0
        self._press_dt = 0

    """
   State getters
   """

    @property
    def state(self) -> State:
        return self._state

    def pressed(self) -> bool:
        return self._state == State.PRESSED

    def pressed_twice(self) -> bool:
        return self._state == State.PRESSED_TWICE

    def released(self) -> bool:
        return self._state == State.RELEASED

    def released_slow(self) -> bool:
        return self._state == State.RELEASED_SLOW

    """
   Manual input
   """

    def press(self):
        now = time.time()
        self._press_flag = True
        self._press_dt = now - self._press_t
        self._press_t = now

    def release(self):
        self._release_flag = True

    """
   MIDI input
   """

    def map_midi_press(self, msg: Message = None, omni=False, **kwargs):
        if msg is None:
            msg = Message(**kwargs)
        self._midi_map.append((msg, True, omni))

    def map_midi_release(self, msg: Message = None, omni=False, **kwargs):
        if msg is None:
            msg = Message(**kwargs)
        self._midi_map.append((msg, False, omni))

    def add_midi_message(self, msg: Message):
        for map_msg, press, omni in self._midi_map:
            if map_msg.channel != map_msg.channel and not omni:
                continue
            if (
                msg.is_cc()
                and map_msg.is_cc()
                and msg.control == map_msg.control
                and msg.value == map_msg.value
            ) or (
                is_note_on_or_note_off(msg)
                and is_note_on_or_note_off(map_msg)
                and msg.note == map_msg.note
            ):
                if press:
                    self.press()
                else:
                    self.release()

    """
   Callback interface
   """

    def set_callback(self, state: State, callback: Callable):
        self._callbacks[state] = callback

    def set_callback_pressed(self, callback: Callable):
        self._callbacks[State.PRESSED] = callback

    def set_callback_pressed_twice(self, callback: Callable):
        self._callbacks[State.PRESSED_TWICE] = callback

    def set_callback_released(self, callback: Callable):
        self._callbacks[State.RELEASED] = callback

    def set_callback_released_slow(self, callback: Callable):
        self._callbacks[State.RELEASED_SLOW] = callback

    def fire_callbacks(self):
        if self.poll():
            try:
                self._callbacks[self._state]()
            except KeyError:
                pass

    """
   Polling interface
   """

    def poll(self) -> bool:
        if self._press_flag:
            self._press_flag = False
            self._release_flag = False
            self._state = State.PRESSED
            return True

        updated = False

        if self._press_t > 0 and self._release_flag:
            dt = time.time() - self._press_t
            if dt > Footswitch.RELEASE_SLOW_SEC:
                self._state = State.RELEASED_SLOW
                updated = True
            elif dt > Footswitch.PRESS_TWICE_SEC:
                self._state = State.RELEASED
                updated = True
        elif self._press_dt > 0 and self._press_dt < Footswitch.PRESS_TWICE_SEC:
            self._state = State.PRESSED_TWICE
            updated = True
        if updated:
            self._press_t = 0
            self._press_dt = 0

        return updated

    """
   Convenience methods
   """

    def process(self, msgs: List[Union[bytes, Message]]):
        for msg in msgs:
            if not isinstance(msg, Message):
                msg = Message.from_bytes(msg)
            self.add_midi_message(msg)
        self.fire_callbacks()

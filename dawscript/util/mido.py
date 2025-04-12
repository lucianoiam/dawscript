# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

from typing import List

from mido import Message


def make_cc(*args, **kwargs) -> Message:
    return Message("control_change", *args, **kwargs)


def make_note_on(*args, **kwargs) -> Message:
    return Message("note_on", *args, **kwargs)


def make_note_off(*args, **kwargs) -> Message:
    return Message("note_off", *args, **kwargs)


def make_midi_messages(midi: List[bytes]) -> List[Message]:
    return [Message.from_bytes(msg_bytes) for msg_bytes in midi]


def is_note_on_or_note_off(msg: Message) -> bool:
    return msg.type.startswith("note_")

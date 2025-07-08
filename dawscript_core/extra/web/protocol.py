# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

import json
import re
from enum import Enum
from typing import Any, Dict

_host_obj: Dict[str, Any] = {}

DEBUG = False
if DEBUG:
    REPR_PATTERN = r"^repr = .+$"
else:
    REPR_PATTERN = r"^handle_[0-9a-fA-F]{8}$"

JS_NUMBER_MAX_VALUE = 1.7976931348623157e308


def replace_inf(data):
    if isinstance(data, float):
        if data == float("inf"):
            return JS_NUMBER_MAX_VALUE
        elif data == -float("inf"):
            return -JS_NUMBER_MAX_VALUE
    elif isinstance(data, list):
        return [replace_inf(item) for item in data]
    elif isinstance(data, dict):
        return {key: replace_inf(value) for key, value in data.items()}

    return data


class ReprJSONDecoder(json.JSONDecoder):
    def decode(self, s, **kwargs):
        value = super().decode(s, **kwargs)

        return self._transform(value)

    def _transform(self, value):
        if isinstance(value, list):
            return [self._transform(val) for val in value]
        elif isinstance(value, dict):
            return {key: self._transform(val) for key, val in value.items()}
        elif isinstance(value, str) and re.match(REPR_PATTERN, value):
            return _host_obj[value]

        return value


class ReprJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value

        try:
            return super().default(obj)
        except TypeError:
            if DEBUG:
                key = f"repr = {repr(obj)}"
            else:
                repr_hash = _d2b_hash(repr(obj))
                key = f"handle_{(repr_hash & 0xFFFFFFFF):08x}"
            _host_obj[key] = obj
            return key


def _d2b_hash(string):
    hash_value = 0
    for char in string:
        hash_value = (31 * hash_value + ord(char)) & 0xFFFFFFFF
        if hash_value >= 0x80000000:
            hash_value -= 0x100000000
    return hash_value

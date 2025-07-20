# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

import json
import re
from enum import Enum
from typing import Any, Dict

from dawscript_core import host

LOG_TAG = "protocol.py"
HANDLE_PREFIX = '@H:'
JS_NUMBER_MAX_VALUE = 1.7976931348623157e308

_host_obj: Dict[str, Any] = {}


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


class JSONDecoder(json.JSONDecoder):
    def decode(self, s, **kwargs):
        value = super().decode(s, **kwargs)

        return self._transform(value)

    def _transform(self, value):
        if isinstance(value, list):
            return [self._transform(val) for val in value]
        elif isinstance(value, dict):
            return {key: self._transform(val) for key, val in value.items()}
        elif isinstance(value, str) and value.startswith(HANDLE_PREFIX):
            try:
                return _host_obj[value]
            except KeyError:
                host.log(f"{LOG_TAG} JSONDecoder._transform(): key '{value}' does not exist")

        return value


class JSONEncoder(json.JSONEncoder):
    get_object_id = repr

    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value

        try:
            return super().default(obj)
        except TypeError:
            key = HANDLE_PREFIX + JSONEncoder.get_object_id(obj)
            _host_obj[key] = obj
            return key

// SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
// SPDX-License-Identifier: MIT

const dawscript = (() => {
  function connect({ on_connect = null, on_disconnect = null } = {}) {
    _connect(...arguments);
  }

  const host = Object.freeze({
    get_tracks: async function () {
      return await _call("get_tracks");
    },

    get_track: async function (name) {
      return await _call("get_track", name);
    },

    is_track_mute: async function (track) {
      return await _call("is_track_mute", track);
    },

    set_track_mute: async function (track, mute) {
      await _call("set_track_mute", track, mute);
    },

    add_track_mute_listener: async function (track, listener) {
      await _call("add_track_mute_listener", track, listener);
    },

    del_track_mute_listener: async function (track, listener) {
      await _call("del_track_mute_listener", track, listener);
    },

    get_track_volume: async function (track) {
      return await _call("get_track_volume", track);
    },

    set_track_volume: async function (track, volume_db) {
      await _call("set_track_volume", track, volume_db);
    },

    add_track_volume_listener: async function (track, listener) {
      await _call("add_track_volume_listener", track, listener);
    },

    del_track_volume_listener: async function (track, listener) {
      await _call("del_track_volume_listener", track, listener);
    },

    get_track_pan: async function (track) {
      return await _call("get_track_pan", track);
    },

    set_track_pan: async function (track, pan) {
      await _call("set_track_pan", track, pan);
    },

    add_track_pan_listener: async function (track, listener) {
      await _call("add_track_pan_listener", track, listener);
    },

    del_track_pan_listener: async function (track, listener) {
      await _call("del_track_pan_listener", track, listener);
    },

    get_plugin: async function (track, name) {
      return await _call("get_plugin", track, name);
    },

    is_plugin_enabled: async function (plugin) {
      return await _call("is_plugin_enabled", plugin);
    },

    set_plugin_enabled: async function (plugin, enabled) {
      await _call("set_plugin_enabled", plugin, enabled);
    },

    add_plugin_enabled_listener: async function (plugin, listener) {
      await _call("add_plugin_enabled_listener", track, listener);
    },

    del_plugin_enabled_listener: async function (plugin, listener) {
      await _call("del_plugin_enabled_listener", track, listener);
    },

    get_parameter: async function (plugin, name) {
      return await _call("get_parameter", plugin, name);
    },

    get_parameter_range: async function (param) {
      return await _call("get_parameter_range", param);
    },

    get_parameter_value: async function (param) {
      return await _call("get_parameter_value", param);
    },

    set_parameter_value: async function (param, value) {
      await _call("set_parameter_value", param, value);
    },

    add_parameter_value_listener: async function (param, listener) {
      await _call("add_parameter_value_listener", track, listener);
    },

    del_parameter_value_listener: async function (param, listener) {
      await _call("del_parameter_value_listener", track, listener);
    },

    // Helpers

    toggle_track_mute: async function (track) {
      await _call("toggle_track_mute", track);
    },

    toggle_track_mute_by_name: async function (name) {
      await _call("toggle_track_mute_by_name", name);
    },

    toggle_plugin_enabled: async function (plugin) {
      await _call("toggle_plugin_enabled", plugin);
    },
  });

  // Private

  const DEFAULT_WEBSOCKET_PORT = 49152;
  const RECONNECT_WAIT_SEC = 3;

  let _socket = null;
  let _seq = 0;
  let _init_queue = [];
  let _promise_cb = {};
  let _listeners = {};
  let _tp_to_seq = {};

  function _connect(callbacks = {}) {
    const port =
      new URLSearchParams(window.location.search).get("port") ||
      DEFAULT_WEBSOCKET_PORT;
    const url = `ws://${window.location.hostname}:${port}`;

    function create_socket() {
      _socket = new WebSocket(url);

      _socket.onopen = () => {
        console.info("dawscript: connected");

        if (callbacks.on_connect) {
          callbacks.on_connect();
        }

        while (_init_queue.length > 0) {
          const [seq, message] = _init_queue.shift();
          _send(seq, message);
        }
      };

      _socket.onmessage = (event) => {
        const [seq, result] = JSON.parse(event.data);
        _handle(seq, result);
      };

      _socket.onerror = (event) => {
        console.warn(`dawscript: ${event.error}`);
        _socket.close();
        _cleanup();
      };

      _socket.onclose = () => {
        console.info("dawscript: disconnected");

        if (! callbacks.on_disconnect || callbacks.on_disconnect()) {
          setTimeout(create_socket, 1000 * RECONNECT_WAIT_SEC);
        }
      };
    }

    create_socket();
  }

  async function _call(func, ...args) {
    return new Promise((resolve, reject) => {
      const m = func.match(/^(add|del)_([a-z_]+)_listener$/);

      if (
        m &&
        args.length == 2 &&
        typeof args[0] === "string" &&
        typeof args[1] === "function"
      ) {
        const [_, action, prop] = m;
        const target_and_prop = `${args[0]}_${prop}`;
        const listener = args[1];

        args.pop();

        if (action == "add") {
          if (target_and_prop in _tp_to_seq) {
            const seq = _tp_to_seq[target_and_prop];
            _listeners[seq].push(listener);
            resolve();
            return; // already registered with server
          }

          _tp_to_seq[target_and_prop] = _seq;
          _listeners[_seq] = [listener];
        } else if (action == "del") {
          const seq = _tp_to_seq[target_and_prop];
          _listeners[seq] = _listeners[seq].filter((l) => l != listener);

          if (_listeners[seq].length > 0) {
            resolve();
            return; // do not unregister yet
          }

          delete _listeners[target_and_prop];
          delete _tp_to_seq[target_and_prop];

          args.push(seq);
        } else {
          reject(new Error("Invalid argument"));
          return;
        }
      }

      const seq = _seq++;
      const message = JSON.stringify([seq, func, ...args]);

      _promise_cb[seq] = [resolve, reject];

      if (_socket.readyState == WebSocket.OPEN) {
        _send(seq, message);
      } else {
        _init_queue.push([seq, message]);
      }
    });
  }

  function _send(seq, message) {
    try {
      _socket.send(message);
    } catch (error) {
      const [_, reject] = _pop_promise_cb(seq);
      reject(error);
    }
  }

  function _handle(seq, result) {
    if (seq in _listeners && typeof result !== "undefined") {
      for (listener of _listeners[seq]) {
        listener(result);
      }
      return;
    }

    const [resolve, reject] = _pop_promise_cb(seq);

    if (typeof result === "string" && result.startsWith("error:")) {
      reject(new HostError(result.slice(6)));
    } else {
      resolve(result);
    }
  }

  function _pop_promise_cb(seq) {
    const callbacks = _promise_cb[seq];
    delete _promise_cb[seq];
    return callbacks;
  }

  function _cleanup() {
    _socket = null;
    _seq = 0;
    _init_queue = [];
    _promise_cb = {};
    _listeners = {};
    _tp_to_seq = {};
  }

  class HostError extends Error {
    constructor(message) {
      super(`host: ${message}`);
      this.name = this.constructor.name;
    }
  }

  return { host, connect };
})(); // dawscript_host

// SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
// SPDX-License-Identifier: MIT

const dawscript = (() => {
  function connect(callback = (/* [re] */connected) => /* reconnect */true) {
    _connect(...arguments);
  }

  const host = Object.freeze({
    getTracks: async function () {
      return await _call("get_tracks");
    },

    getTrack: async function (name) {
      return await _call("get_track", name);
    },

    isTrackMute: async function (track) {
      return await _call("is_track_mute", track);
    },

    setTrackMute: async function (track, mute) {
      await _call("set_track_mute", track, mute);
    },

    addTrackMuteListener: async function (track, listener) {
      await _call("add_track_mute_listener", track, listener);
    },

    delTrackMuteListener: async function (track, listener) {
      await _call("del_track_mute_listener", track, listener);
    },

    getTrackVolume: async function (track) {
      return await _call("get_track_volume", track);
    },

    setTrackVolume: async function (track, volumeDb) {
      await _call("set_track_volume", track, volumeDb);
    },

    addTrackVolumeListener: async function (track, listener) {
      await _call("add_track_volume_listener", track, listener);
    },

    delTrackVolumeListener: async function (track, listener) {
      await _call("del_track_volume_listener", track, listener);
    },

    getTrackPan: async function (track) {
      return await _call("get_track_pan", track);
    },

    setTrackPan: async function (track, pan) {
      await _call("set_track_pan", track, pan);
    },

    addTrackPanListener: async function (track, listener) {
      await _call("add_track_pan_listener", track, listener);
    },

    delTrackPanListener: async function (track, listener) {
      await _call("del_track_pan_listener", track, listener);
    },

    getPlugin: async function (track, name) {
      return await _call("get_plugin", track, name);
    },

    isPluginEnabled: async function (plugin) {
      return await _call("is_plugin_enabled", plugin);
    },

    setPluginEnabled: async function (plugin, enabled) {
      await _call("set_plugin_enabled", plugin, enabled);
    },

    addPluginEnabledListener: async function (plugin, listener) {
      await _call("add_plugin_enabled_listener", track, listener);
    },

    delPluginEnabledListener: async function (plugin, listener) {
      await _call("del_plugin_enabled_listener", track, listener);
    },

    getParameter: async function (plugin, name) {
      return await _call("get_parameter", plugin, name);
    },

    getParameterRange: async function (param) {
      return await _call("get_parameter_range", param);
    },

    getParameterValue: async function (param) {
      return await _call("get_parameter_value", param);
    },

    setParameterValue: async function (param, value) {
      await _call("set_parameter_value", param, value);
    },

    addParameterValueListener: async function (param, listener) {
      await _call("add_parameter_value_listener", track, listener);
    },

    delParameterValueListener: async function (param, listener) {
      await _call("del_parameter_value_listener", track, listener);
    },

    toggleTrackMute: async function (track) {
      await _call("toggle_track_mute", track);
    },

    toggleTrackMuteByName: async function (name) {
      await _call("toggle_track_mute_by_name", name);
    },

    togglePluginEnabled: async function (plugin) {
      await _call("toggle_plugin_enabled", plugin);
    },
  });

  const DEFAULT_WEBSOCKET_PORT = 49152;
  const RECONNECT_WAIT_SEC = 3;

  let _socket = null;
  let _seq = 0;
  let _promise_cb = {};
  let _listeners = {};
  let _tp_to_add_lstnr_seq = {};

  function _connect(callback) {
    const port =
      new URLSearchParams(window.location.search).get("port") ||
      DEFAULT_WEBSOCKET_PORT;
    const url = `ws://${window.location.hostname}:${port}`;

    function create_socket() {
      _socket = new WebSocket(url);

      _socket.onopen = () => {
        console.info("dawscript: connected");

        if (callback) {
          callback(true);
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

        if (! callback || callback(false)) {
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
        const target = args[0];
        const listener = args.pop();

        if (action == "add") {
          const needs_reg = _add_listener(target, prop, listener, _seq);

          if (! needs_reg) {
            resolve();
            return;
          }
        } else if (action == "del") {
          const add_lstnr_seq = _del_listener(target, prop, listener);

          if (add_lstnr_seq === null) {
            resolve();
            return;
          }

          args.push(add_lstnr_seq);
        } else {
          reject(new Error("Invalid argument"));
          return;
        }
      }

      const seq = _seq++;

      try {
        _promise_cb[seq] = [resolve, reject];
        _socket.send(JSON.stringify([seq, func, ...args]));
      } catch (error) {
        _pop_promise_cb(seq);
        reject(error);
      }
    });
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

  function _add_listener(target, prop, listener, seq) {
    const target_and_prop = `${target}_${prop}`;

    if (target_and_prop in _tp_to_add_lstnr_seq) {
      const add_lstnr_seq = _tp_to_add_lstnr_seq[target_and_prop];
      _listeners[add_lstnr_seq].push(listener);

      return false; // already registered with server
    }

    _tp_to_add_lstnr_seq[target_and_prop] = seq;
    _listeners[seq] = [listener];

    return true;
  }

  function _del_listener(target, prop, listener) {
    const target_and_prop = `${target}_${prop}`;
    const add_lstnr_seq = _tp_to_add_lstnr_seq[target_and_prop];

    _listeners[add_lstnr_seq] = _listeners[add_lstnr_seq]
      .filter((l) => l != listener);

    if (_listeners[add_lstnr_seq].length > 0) {
      return null;  // do not unregister from server yet
    }

    delete _listeners[target_and_prop];
    delete _tp_to_add_lstnr_seq[target_and_prop];

    return add_lstnr_seq;
  }

  function _pop_promise_cb(seq) {
    const callbacks = _promise_cb[seq];
    delete _promise_cb[seq];
    return callbacks;
  }

  function _cleanup() {
    _socket = null;
    _seq = 0;
    _promise_cb = {};
    _listeners = {};
    _tp_to_add_lstnr_seq = {};
  }

  class HostError extends Error {
    constructor(message) {
      super(`host: ${message}`);
      this.name = this.constructor.name;
    }
  }

  return { host, connect };
})(); // dawscript_host

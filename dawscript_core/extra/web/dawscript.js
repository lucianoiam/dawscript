// SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
// SPDX-License-Identifier: MIT

window.dawscript = (() => {

const enableDebugMessages = () => _debug_msg = true;
const connect = (callback = (status) => true) => _connect(callback);

// host/public.py
const host = Object.freeze({
   name: async ()                                        => _call("name"),
   getFaderLabels: async ()                              => _call("get_fader_labels"),
   getTracks: async ()                                   => _call("get_tracks"),
   getTrackType: async (track)                           => _call("get_track_type", track),
   getTrackName: async (track)                           => _call("get_track_name", track),
   isTrackMute: async (track)                            => _call("is_track_mute", track),
   setTrackMute: async (track, mute)                     => _call("set_track_mute", track, mute),
   addTrackMuteListener: async (track, listener)         => _call("add_track_mute_listener", track, listener),
   removeTrackMuteListener: async (track, listener)      => _call("remove_track_mute_listener", track, listener),
   getTrackVolume: async (track)                         => _call("get_track_volume", track),
   setTrackVolume: async (track, volumeDb)               => _call("set_track_volume", track, volumeDb),
   addTrackVolumeListener: async (track, listener)       => _call("add_track_volume_listener", track, listener),
   removeTrackVolumeListener: async (track, listener)    => _call("remove_track_volume_listener", track, listener),
   getTrackPan: async (track)                            => _call("get_track_pan", track),
   setTrackPan: async (track, pan)                       => _call("set_track_pan", track, pan),
   addTrackPanListener: async (track, listener)          => _call("add_track_pan_listener", track, listener),
   removeTrackPanListener: async (track, listener)       => _call("remove_track_pan_listener", track, listener),
   getTrackPlugins: async (track)                        => _call("get_track_plugins", track),
   getTrackPlugin: async (track, name)                   => _call("get_track_plugin", track, name),
   getPluginName: async (plugin)                         => _call("get_plugin_name", plugin),
   isPluginEnabled: async (plugin)                       => _call("is_plugin_enabled", plugin),
   setPluginEnabled: async (plugin, enabled)             => _call("set_plugin_enabled", plugin, enabled),
   addPluginEnabledListener: async (plugin, listener)    => _call("add_plugin_enabled_listener", plugin, listener),
   removePluginEnabledListener: async (plugin, listener) => _call("remove_plugin_enabled_listener", plugin, listener),
   getPluginParameters: async (plugin)                   => _call("get_plugin_parameters", plugin),
   getPluginParameter: async (plugin, name)              => _call("get_plugin_parameter", plugin, name),
   getParameterName: async (param)                       => _call("get_parameter_name", param),
   getParameterRange: async (param)                      => _call("get_parameter_range", param),
   getParameterValue: async (param)                      => _call("get_parameter_value", param),
   setParameterValue: async (param, value)               => _call("set_parameter_value", param, value),
   addParameterValueListener: async (param, listener)    => _call("add_parameter_value_listener", param, listener),
   removeParameterValueListener: async (param, listener) => _call("remove_parameter_value_listener", param, listener),
   getTrackByName: async (name)                          => _call("get_track_by_name", name),
   toggleTrackMute: async (track)                        => _call("toggle_track_mute", track),
   toggleTrackMuteByName: async (name)                   => _call("toggle_track_mute_by_name", name),
   getTrackPluginByName: async (track, name)             => _call("get_track_plugin_by_name", track, name),
   getPluginParameterByName: async (plugin, name)        => _call("get_plugin_parameter_by_name", plugin, name),
   togglePluginEnabled: async (plugin)                   => _call("toggle_plugin_enabled", plugin),
});

const TrackType = Object.freeze({
   AUDIO : 0,
   MIDI  : 1,
   OTHER : 2
});


// Private

const DEFAULT_WEBSOCKET_PORT = 49152;
const RECONNECT_WAIT_SEC = 3;
const CONSOLE_TAG = 'dawscript';

let _debug_msg = false;
let _socket = null;
let _seq = 0;
let _init_queue = [];
let _promise_cb = {};
let _listeners = {};
let _tp_to_listener_seq = {};

function _connect(callback) {
   const port =
      new URLSearchParams(window.location.search).get("port") ||
      DEFAULT_WEBSOCKET_PORT;
   const url = `ws://${window.location.hostname}:${port}`;

   function create_socket() {
      _socket = new WebSocket(url);

      _socket.onopen = () => {
         _info("connected");

         if (callback) {
            callback(true);
         }

         while (_init_queue.length > 0) {
            _send(_init_queue.shift());
         }
      };

      _socket.onmessage = (event) => _handle(event.data);

      _socket.onerror = (error) => {
         _socket.close();
         _cleanup();
      };

      _socket.onclose = (event) => {
         _warn("disconnected", event.code, event.reason);

         if (! callback || callback(false)) {
            setTimeout(create_socket, 1000 * RECONNECT_WAIT_SEC);
         }
      };
   }

   create_socket();
}

async function _call(func_name, ...args) {
   return new Promise((resolve, reject) => {
      const m = func_name.match(/^(add|remove)_([a-z_]+)_listener$/);

      if (
         m &&
         args.length == 2 &&
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
         } else if (action == "remove") {
            const listener_seq = _remove_listener(target, prop, listener);

            if (listener_seq === null) {
               resolve();
               return;
            }

            args = [listener_seq];
         } else {
            reject(new Error("Invalid argument"));
            return;
         }
      }

      const seq = _seq++;
      const message = [seq, func_name, ...args];
      const wait_reply = ! func_name.match(/^set_([a-z_]+)$/);

      if (wait_reply) {
         _promise_cb[seq] = [resolve, reject];
      }

      if (_socket && _socket.readyState == WebSocket.OPEN) {
         _debug(`→ ${seq}`, message);
         _send(message);
      } else {
         _debug(`↛ ${seq}`, message);
         _init_queue.push(message);
      }
   });
}

function _send(message, wait) {
   try {
      _socket.send(JSON.stringify(message, (_, value) => {
         if (value === Infinity) return Number.MAX_VALUE;
         if (value === -Infinity) return -Number.MAX_VALUE;
         return value;
      }));
   } catch (error) {
      const callbacks = _pop_promise_cb(message[0]);

      if (callbacks) {
         const [_, reject] = callbacks;
         reject(error);
      }
   }
}

function _handle(message) {
   const [seq, result] = JSON.parse(message, (_, value) => {
      if (value === Number.MAX_VALUE) return Infinity;
      if (value === -Number.MAX_VALUE) return -Infinity;
      return value;
   });

   if (seq in _listeners && typeof result !== "undefined") {
      _debug(`⬿ ${seq}`, result);

      for (listener of _listeners[seq]) {
         listener(result);
      }

      return;
   }

   if (! (seq in _promise_cb)) {
      _warn(`⬿ ${seq}`, result);
      return;
   }

   const [resolve, reject] = _pop_promise_cb(seq);

   _debug(`← ${seq}`, typeof result !== 'undefined' ? result : '<ack>');

   if (typeof result === "string" && result.startsWith("error:")) {
      reject(new HostError(result.slice(6)));
   } else {
      resolve(result);
   }
}

function _add_listener(target, prop, listener, seq) {
   const key_tp = `${target}_${prop}`;

   if (key_tp in _tp_to_listener_seq) {
      const listener_seq = _tp_to_listener_seq[key_tp];
      _listeners[listener_seq].push(listener);

      return false; // already registered with server
   }

   _tp_to_listener_seq[key_tp] = seq;
   _listeners[seq] = [listener];

   return true;
}

function _remove_listener(target, prop, listener) {
   const key_tp = `${target}_${prop}`;
   const listener_seq = _tp_to_listener_seq[key_tp];

   if (listener_seq in _listeners) {
      _listeners[listener_seq] = _listeners[listener_seq]
         .filter((l) => l != listener);

      if (_listeners[listener_seq].length > 0) {
         return null;  // do not unregister from server yet
      }
   }

   delete _listeners[key_tp];
   delete _tp_to_listener_seq[key_tp];

   return listener_seq;
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
   _tp_to_listener_seq = {};
}  

function _debug(...message) {
   if (_debug_msg) console.debug(`[${CONSOLE_TAG}]`, ...message);
}

function _info(...message) {
   console.info(`[${CONSOLE_TAG}]`, ...message);
}

function _warn(...message) {
   console.warn(`[${CONSOLE_TAG}]`, ...message);
}

class HostError extends Error {
   constructor(message) {
      super(message);
      this.name = this.constructor.name;
   }
}

return Object.freeze({
   enableDebugMessages,
   connect,
   host,
   TrackType
});

})(); // dawscript

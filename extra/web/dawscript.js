// SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
// SPDX-License-Identifier: MIT

const dawscript = (() => {

// host/public.py
const host = Object.freeze({
   getTracks: async ()                                 => _call("get_tracks"),
   getTrackName: async (track)                         => _call("get_track_name", track),
   isTrackMute: async (track)                          => _call("is_track_mute", track),
   setTrackMute: async (track, mute)                   => _call("set_track_mute", track, mute),
   addTrackMuteListener: async (track, listener)       => _call("add_track_mute_listener", track, listener),
   delTrackMuteListener: async (track, listener)       => _call("del_track_mute_listener", track, listener),
   getTrackVolume: async (track)                       => _call("get_track_volume", track),
   setTrackVolume: async (track, volumeDb)             => _call("set_track_volume", track, volumeDb),
   addTrackVolumeListener: async (track, listener)     => _call("add_track_volume_listener", track, listener),
   delTrackVolumeListener: async (track, listener)     => _call("del_track_volume_listener", track, listener),
   getTrackPan: async (track)                          => _call("get_track_pan", track),
   setTrackPan: async (track, pan)                     => _call("set_track_pan", track, pan),
   addTrackPanListener: async (track, listener)        => _call("add_track_pan_listener", track, listener),
   delTrackPanListener: async (track, listener)        => _call("del_track_pan_listener", track, listener),
   getTrackPlugins: async (track)                      => _call("get_track_plugins", track),
   getTrackPlugin: async (track, name)                 => _call("get_track_plugin", track, name),
   getPluginName: async (plugin)                       => _call("get_plugin_name", plugin),
   isPluginEnabled: async (plugin)                     => _call("is_plugin_enabled", plugin),
   setPluginEnabled: async (plugin, enabled)           => _call("set_plugin_enabled", plugin, enabled),
   addPluginEnabledListener: async (plugin, listener)  => _call("add_plugin_enabled_listener", track, listener),
   delPluginEnabledListener: async (plugin, listener)  => _call("del_plugin_enabled_listener", track, listener),
   getPluginParameters: async (plugin)                 => _call("get_plugin_parameters", plugin),
   getPluginParameter: async (plugin, name)            => _call("get_plugin_parameter", plugin, name),
   getParameterName: async (param)                     => _call("get_parameter_name", param),
   getParameterRange: async (param)                    => _call("get_parameter_range", param),
   getParameterValue: async (param)                    => _call("get_parameter_value", param),
   setParameterValue: async (param, value)             => _call("set_parameter_value", param, value),
   addParameterValueListener: async (param, listener)  => _call("add_parameter_value_listener", track, listener),
   delParameterValueListener: async (param, listener)  => _call("del_parameter_value_listener", track, listener),
   getTrack: async (name)                              => _call("get_track", name),
   toggleTrackMute: async (track)                      => _call("toggle_track_mute", track),
   toggleTrackMuteByName: async (name)                 => _call("toggle_track_mute_by_name", name),
   getTrackPlugin: async (track, name)                 => _call("get_track_plugin", track, name),
   getPluginParameter: async (plugin, name)            => _call("get_plugin_parameter", plugin, name),
   togglePluginEnabled: async (plugin)                 => _call("toggle_plugin_enabled", plugin),
});

function connect(callback = (connected) => /* reconnect */true) {
   _connect(...arguments);
}


// Private

const DEFAULT_WEBSOCKET_PORT = 49152;
const RECONNECT_WAIT_SEC = 3;

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
         console.info("dawscript: connected");

         if (callback) {
            callback(true);
         }

         while (_init_queue.length > 0) {
            _send(_init_queue.shift());
         }
      };

      _socket.onmessage = (event) => _handle(event.data);

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

async function _call(func_name, ...args) {
   return new Promise((resolve, reject) => {
      const m = func_name.match(/^(add|del)_([a-z_]+)_listener$/);

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
            const listener_seq = _del_listener(target, prop, listener);

            if (listener_seq === null) {
               resolve();
               return;
            }

            args.push(listener_seq);
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
         _send(message);
      } else {
         _init_queue.push(message);
      }
   });
}

function _send(message, wait) {
   try {
      _socket.send(JSON.stringify(message));
   } catch (error) {
      const callbacks = _pop_promise_cb(message[0]);

      if (callbacks) {
         const [_, reject] = callbacks;
         reject(error);
      }
   }
}

function _handle(message) {
   const [seq, result] = JSON.parse(message);

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

function _del_listener(target, prop, listener) {
   const key_tp = `${target}_${prop}`;
   const listener_seq = _tp_to_listener_seq[key_tp];

   _listeners[listener_seq] = _listeners[listener_seq]
      .filter((l) => l != listener);

   if (_listeners[listener_seq].length > 0) {
      return null;  // do not unregister from server yet
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

class HostError extends Error {
   constructor(message) {
      super(`host: ${message}`);
      this.name = this.constructor.name;
   }
}

return Object.freeze({ host, connect });

})(); // dawscript

// SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
// SPDX-License-Identifier: MIT

const dawscript_host = (() => {
const public = Object.freeze({

   get_tracks: async function() {
      return await _call('get_tracks');
   },

   get_track: async function(name) {
      return await _call('get_track', name);
   },

   is_track_mute: async function(track) {
      return await _call('is_track_mute', track);
   },

   set_track_mute: async function(track, mute) {
      await _call('set_track_mute', track, mute);
   },

   set_track_mute_listener: async function(track, listener) {
      await _call('set_track_mute_listener', track, listener);
   },

   get_track_volume: async function(track) {
      return await _call('get_track_volume', track);
   },

   set_track_volume: async function(track, volume_db) {
      await _call('set_track_volume', track, volume_db);
   },

   set_track_volume_listener: async function(track, listener) {
      await _call('set_track_volume_listener', track, listener);
   },

   get_track_pan: async function(track) {
      return await _call('get_track_pan', track);
   },

   set_track_pan: async function(track, pan) {
      await _call('set_track_pan', track, pan);
   },

   set_track_pan_listener: async function(track, listener) {
      await _call('set_track_pan_listener', track, listener);
   },

   get_plugin: async function(track, name) {
       return await _call('get_plugin', track, name);
   },

   is_plugin_enabled: async function(plugin) {
       return await _call('is_plugin_enabled', plugin);
   },

   set_plugin_enabled: async function(plugin, enabled) {
      await _call('set_plugin_enabled', plugin, enabled);
   },

   set_plugin_enabled_listener: async function(plugin, listener) {
      await _call('set_plugin_enabled_listener', plugin, listener);
   },

   get_parameter: async function(plugin, name) {
       return await _call('get_parameter', plugin, name);
   },

   get_parameter_range: async function(param) {
       return await _call('get_parameter_range', param);
   },

   get_parameter_value: async function(param) {
       return await _call('get_parameter_value', param);
   },

   set_parameter_value: async function(param, value) {
      await _call('set_parameter_value', param, value);
   },

   set_parameter_value_listener: async function(param, listener) {
      await _call('set_parameter_value_listener', param, listener);
   }
});

const DEFAULT_WEBSOCKET_PORT = 49152;

const _init_queue = [];
const _promise_cb = {};
const _listeners = {};
const _socket = _create_websocket();

let _message_seq = 0;

function _call(func, ...args) {
   return new Promise((resolve, reject) => {
      const seq = _message_seq++;

      if (/^set_[a-z_]+_listener$/.test(func)
                           && args.length == 2
                           && typeof args[0] === 'string'
                           && typeof args[1] === 'function') {
         _listeners[seq] = args[1];
         args.pop();
      }

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
      delete _listeners[seq];
      const [_, reject] = _pop_promise_cb(seq);
      reject(error);
   }
}

function _handle(seq, result) {
   if (seq in _listeners) {
      if (result !== null) { // discard set_xxx_listener() ack
         _listeners[seq](result);
      }
      return;   
   }

   const [resolve, reject] = _pop_promise_cb(seq);

   if (typeof result === 'string' && result.startsWith('error:')) {
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

function _create_websocket() {
   const port = new URLSearchParams(window.location.search).get('port')
                  || DEFAULT_WEBSOCKET_PORT;
   const socket = new WebSocket(`ws://${window.location.hostname}:${port}`);

   socket.onopen = () => {
      console.log('host: connected');

      while (_init_queue.length > 0) {
         const [seq, message] = _init_queue.shift();
         _send(seq, message);
      }
   };

   socket.onmessage = (event) => {
      const [seq, result] = JSON.parse(event.data);
      _handle(seq, result);
   };

   socket.onclose = () => {
      console.log('host: disconnected');
   };

   socket.onerror = (error) => {
      console.error(error);
   };

   return socket;
}

class HostError extends Error {
   constructor(message) {
      super(`host: ${message}`);
      this.name = this.constructor.name;
   }
}

return public;

})(); // dawscript_host

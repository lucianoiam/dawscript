// SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
// SPDX-License-Identifier: MIT

const _callbacks = {};
const _queue = [];
const _socket = _create_websocket();
let _seq = 0;

async function get_tracks() {
   return await _call('get_tracks');
}

async function get_track(name) {
   return await _call('get_track', name);
}

async function is_track_mute(track) {
   return await _call('is_track_mute', track);
}

async function set_track_mute(track, mute) {
   await _call('set_track_mute', track, mute);
} 

async function set_track_mute_listener(track, listener) {
   await _call('set_track_mute_listener', track, listener);
}

async function get_track_volume(track) {
   return await _call('get_track_volume', track);
}  

async function set_track_volume(track, volume_db) {
   await _call('set_track_volume', track, volume_db);
}

async function set_track_volume_listener(track, listener) {
   await _call('set_track_volume_listener', track, listener);
}

async function get_track_pan(track) {
   return await _call('get_track_pan', track);
}

async function set_track_pan(track, pan) {
   await _call('set_track_pan', track, pan);
}

async function set_track_pan_listener(track, listener) {
   await _call('set_track_pan_listener', track, listener);
}

async function get_plugin(track, name) {
    return await _call('get_plugin', track, name);
}

async function is_plugin_enabled(plugin) {
    return await _call('is_plugin_enabled', plugin);
}

async function set_plugin_enabled(plugin, enabled) {
   await _call('set_plugin_enabled', plugin, enabled);
}

async function set_plugin_enabled_listener(plugin, listener) {
   await _call('set_plugin_enabled_listener', plugin, listener);
}

async function get_parameter(plugin, name) {
    return await _call('get_parameter', plugin, name);
}

async function get_parameter_range(param) {
    return await _call('get_parameter_range', param);
}

async function get_parameter_value(param) {
    return await _call('get_parameter_value', param);
}

async function set_parameter_value(param, value) {
   await _call('set_parameter_value', param, value);
}

async function set_parameter_value_listener(param, listener) {
   await _call('set_parameter_value_listener', param, listener);
}

function _call(func, ...args) {
   return new Promise((resolve, reject) => {
      const seq = _seq++;
      const message = JSON.stringify([seq, func, ...args]);

      _callbacks[seq] = [resolve, reject];

      if (_socket.readyState == WebSocket.OPEN) {
         _send(seq, message);
      } else {
         _queue.push([seq, message]);
      }
   });
}

function _send(seq, message) {
   try {
      _socket.send(message);
   } catch (error) {
      const [_, reject] = _pop_callbacks(seq);
      reject(error);
   }
}

function _handle(seq, result) {
   const [resolve, reject] = _pop_callbacks(seq);

   if (typeof result === 'string' && result.startsWith('error:')) {
      reject(new HostError(result.slice(6)));
   } else {
      resolve(result);
   }
}

function _pop_callbacks(seq) {
   const callbacks = _callbacks[seq];
   delete _callbacks[seq];
   return callbacks;
}

const DEFAULT_PORT_WEBSOCKET = 49152;

function _create_websocket() {
   const port = new URLSearchParams(window.location.search).get('port')
                  || DEFAULT_PORT_WEBSOCKET;
   const socket = new WebSocket(`ws://localhost:${port}`);

   socket.onopen = () => {
      console.log('host: connected');

      while (_queue.length > 0) {
         const [seq, message] = _queue.shift();
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

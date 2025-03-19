// SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
// SPDX-License-Identifier: MIT

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

async function _call(func, ...args) {
   // TODO
}

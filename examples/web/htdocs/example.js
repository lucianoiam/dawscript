// SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
// SPDX-License-Identifier: MIT

const { host, connect } = dawscript;

const input = document.createElement("input");
input.type = "text";
input.placeholder = "Check dawscript.js for all available functions";
input.addEventListener("keydown", (ev) => {
  if (ev.key === "Enter") on_click_run();
});
document.body.appendChild(input);

const run = document.createElement("button");
run.textContent = "Run";
run.addEventListener("click", on_click_run);
document.body.appendChild(run);

const output = document.createElement("pre");
document.body.appendChild(output);

const get_tracks = document.createElement("button");
get_tracks.textContent = "Example: get_tracks()";
get_tracks.addEventListener("click", on_click_get_tracks);
document.body.appendChild(get_tracks);

const slider = document.createElement("input");
slider.style.display = "block";
slider.type = "range";
slider.min = -68;
slider.max = 6;
slider.addEventListener("input", on_slider_input);

connect({ on_connect: add_host_listeners });


async function on_click_run() {
  try {
    output.textContent = await eval("host." + input.value);
  } catch (error) {
    output.textContent = error.message;
  }
}


let last_track = null;


async function on_click_get_tracks() {
  if (last_track != null) {
    return;
  }

  const tracks = await host.get_tracks();

  if (tracks.length == 0) {
    output.textContent = "No tracks found";
    return;
  }

  output.textContent = tracks;
  last_track = tracks[tracks.length - 1];

  slider.value = await host.get_track_volume(last_track);
  document.body.appendChild(slider);

  add_host_listeners();
}


function on_slider_input() {
  host.set_track_volume(last_track, parseFloat(slider.value));
}


function add_host_listeners() {
  if (last_track) {
    host.add_track_volume_listener(last_track, (vol) => {
      slider.value = vol;
    });
  }
}

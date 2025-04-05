// SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
// SPDX-License-Identifier: MIT

const input = document.createElement('input');
input.type = 'text';
input.placeholder = 'Check host.js for all available functions';
input.addEventListener('keydown', (ev) => { if (ev.key === 'Enter') on_click_run() });
document.body.appendChild(input);

const run = document.createElement('button');
run.textContent = 'Run';
run.addEventListener('click', on_click_run);
document.body.appendChild(run);

const output = document.createElement('pre');
document.body.appendChild(output);

const get_tracks = document.createElement('button');
get_tracks.textContent = 'Example: get_tracks()';
get_tracks.addEventListener('click', on_click_get_tracks);
document.body.appendChild(get_tracks);


function on_click_run() {
    try {
        const result = eval('dawscript_host.' + input.value);

        if (result instanceof Promise) {
            result.then((asyncResult) => {
                output.textContent = asyncResult;
            }).catch((error) => {
                output.textContent = error.message;
            });
        } else {
            output.textContent = result;
        }
    } catch (error) {
        output.textContent = error.message;
    }
}


let last_track = null;

async function on_click_get_tracks() {
    if (last_track != null) {
        return;
    }

    const tracks = await dawscript_host.get_tracks();

    if (tracks.length == 0) {
        output.textContent = 'No tracks found';
        return;
    }

    last_track = tracks[tracks.length - 1];

    const slider = document.createElement('input');
    slider.style.display = 'block';
    slider.type = 'range';
    slider.min = -68;
    slider.max = 6;
    slider.value = await dawscript_host.get_track_volume(last_track);

    slider.addEventListener('input', (ev) => {
        dawscript_host.set_track_volume(last_track, parseFloat(slider.value));
    });

    dawscript_host.add_track_volume_listener(last_track, (vol) => {
        slider.value = vol;
    });

    document.body.appendChild(slider);
}

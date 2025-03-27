// SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
// SPDX-License-Identifier: MIT

const input = document.createElement('input');
input.placeholder = 'Check host.js for all available functions. For example: get_tracks()';
input.addEventListener('keydown', (ev) => { if (ev.key === 'Enter') run() });

const output = document.createElement('pre');

const button = document.createElement('button');
button.textContent = 'Run';
button.addEventListener('click', run);

[input, output, button].forEach((element) => {
    document.body.appendChild(element);
});

function run() {
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

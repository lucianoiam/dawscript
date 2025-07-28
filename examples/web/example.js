// SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
// SPDX-License-Identifier: MIT

const { connect, disconnect, host } = dawscript;

window.addEventListener('DOMContentLoaded', () => {
   window.onerror = log;
   window.onunhandledrejection = ev => log(ev.reason);

   const editor = window.ace.edit(document.getElementById('editor'));
   const functions = Object.values(host).map(fn => ' * async host.' + fn.name + '()');
   const defaultText = get_function_body(default_code) + '\n\n\n'
           + `/**\n * ${functions.length} functions available in dawscript.js\n *\n`
           + functions.join('\n')
           + '\n */\n';

   editor.setValue(defaultText);
   editor.gotoLine(1);
   editor.focus();
   editor.setTheme('ace/theme/monokai');
   editor.session.setMode('ace/mode/javascript');

   document.getElementById('load-demo').addEventListener('click', () => {
      editor.setValue(get_function_body(demo_code));
      editor.gotoLine(1);
   });

   document.getElementById('run').addEventListener('click', () => {
      try {
         const controls = document.getElementById('controls');
         if (controls.children.length >= 4) {
            controls.children[3].remove();
         }
         disconnect();
         eval(editor.getValue());
      } catch (e) {
         log('Error: ' + e.message);
      }
   });
});

function get_function_body(fn) {
   return fn.toString()
      .split('\n')
      .slice(1, -1)
      .map(line => line.startsWith('   ') ? line.slice(3) : line)
      .join('\n');
}

function default_code() {
   host.name().then(log);
   connect();
}

function demo_code() {
   connect(async (success) => {
      if (success) {
         const tracks = await host.getTracks();
         if (tracks.length > 0) {
            const track = tracks[tracks.length - 1];
            const vol = await host.getTrackVolume(track);
            log('Volume of last track: ' + vol);
            const slider = document.createElement('input');
            document.getElementById('controls').appendChild(slider);
            slider.style.width = '200px';
            slider.type = 'range';
            slider.min = 0;
            slider.max = 1;
            slider.step = 0.01;
            slider.value = vol;
            slider.addEventListener('input', async () => {
               const vol = parseFloat(slider.value);
               host.setTrackVolume(track, vol);
               log('Volume of last track set to: ' + vol);
            });
            host.addTrackVolumeListener(track, (vol) => {
               slider.value = vol;
               log('Volume of last track changed: ' + vol);
            });
         } else {
            log('No tracks found');
         }
      } else {
         log('Lost connection to DAW');
      }
      return true;
   });

};

function log(message) {
   document.getElementById('log').textContent = message;
}

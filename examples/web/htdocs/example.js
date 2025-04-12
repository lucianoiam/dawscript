// SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
// SPDX-License-Identifier: MIT

const { host, connect } = dawscript;

const code = document.createElement("input");
code.type = "text";
code.placeholder = "Available functions in dawscript.js";
code.addEventListener("keydown", (ev) => {
  if (ev.key === "Enter") onRunClick();
});
document.body.appendChild(code);

const run = document.createElement("button");
run.textContent = "Run";
run.addEventListener("click", onRunClick);
document.body.appendChild(run);

const output = document.createElement("pre");
document.body.appendChild(output);

const getTracks = document.createElement("button");
getTracks.textContent = "getTracks()";
getTracks.addEventListener("click", onGetTracksClick);
document.body.appendChild(getTracks);

const trackVolume = document.createElement("input");
trackVolume.style.display = "block";
trackVolume.type = "range";
trackVolume.min = -68;
trackVolume.max = 6;
trackVolume.addEventListener("input", onTrackVolumeInput);

connect(connectCallback);



let lastTrack = null;


function connectCallback(connected) {
  if (connected) {
    addHostListeners();
  }

  return true;
}


function addHostListeners() {
  if (lastTrack) {
    host.addTrackVolumeListener(lastTrack, (vol) => {
      trackVolume.value = vol;
    });
  }
}


async function onRunClick() {
  try {
    output.textContent = await eval("host." + code.value);
  } catch (error) {
    output.textContent = error.message;
  }
}


async function onGetTracksClick() {
  if (lastTrack != null) {
    return;
  }

  const tracks = await host.getTracks();

  if (tracks.length == 0) {
    output.textContent = "No tracks found";
    return;
  }

  output.textContent = tracks;
  lastTrack = tracks[tracks.length - 1];

  trackVolume.value = await host.getTrackVolume(lastTrack);
  document.body.appendChild(trackVolume);

  addHostListeners();
}


function onTrackVolumeInput() {
  host.setTrackVolume(lastTrack, parseFloat(trackVolume.value));
}

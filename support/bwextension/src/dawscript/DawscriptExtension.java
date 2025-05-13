// SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
// SPDX-License-Identifier: MIT

package dawscript;

import java.io.File;

import com.bitwig.extension.api.util.midi.ShortMidiMessage;
import com.bitwig.extension.callback.ShortMidiMessageReceivedCallback;
import com.bitwig.extension.controller.api.ControllerHost;
import com.bitwig.extension.controller.api.Transport;
import com.bitwig.extension.controller.ControllerExtension;
import py4j.GatewayServer;

import dawscript.BitwigExtensionLocator;
import dawscript.PythonScript;

public class DawscriptExtension extends ControllerExtension
{
   private static final String EXTENSION_FILENAME = "dawscript.bwextension";
   private static final String PYTHON_SCRIPT_FILENAME = "dawscript.py";

   private Transport transport;
   private GatewayServer gatewayServer;
   private PythonScript pythonScript;

   protected DawscriptExtension(final DawscriptExtensionDefinition definition, final ControllerHost host)
   {
      super(definition, host);
   }

   @Override
   public void init()
   {
      final ControllerHost host = getHost();      

      transport = host.createTransport();
      //host.getMidiInPort(0).setMidiCallback((ShortMidiMessageReceivedCallback)msg -> onMidi0(msg));
      //host.getMidiInPort(0).setSysexCallback((String data) -> onSysex0(data));

      try {
         gatewayServer = new GatewayServer(this);
         gatewayServer.start();

         pythonScript = new PythonScript();
         File script = BitwigExtensionLocator.getPath(EXTENSION_FILENAME)
            .toPath()
            .toRealPath()
            .getParent()
            .resolve(PYTHON_SCRIPT_FILENAME)
            .toFile();
         //pythonScript.start(script);

         //host.showPopupNotification("dawscript Initialized");
      } catch (Exception e) {
         host.showPopupNotification(e.getMessage());
      }
   }

   @Override
   public void exit()
   {
      pythonScript.stop();
      pythonScript = null;

      gatewayServer.shutdown();
      gatewayServer = null;

      // TODO: Perform any cleanup once the driver exits
      // For now just show a popup notification for verification that it is no longer running.
      getHost().showPopupNotification("dawscript Exited");
   }

   @Override
   public void flush()
   {
      // TODO Send any updates you need here.
   }

   /** Called when we receive short MIDI message on port 0. */
   private void onMidi0(ShortMidiMessage msg) 
   {
      // TODO: Implement your MIDI input handling code here.
   }

   /** Called when we receive sysex MIDI message on port 0. */
   private void onSysex0(final String data) 
   {
      // MMC Transport Controls:
      if (data.equals("f07f7f0605f7"))
            transport.rewind();
      else if (data.equals("f07f7f0604f7"))
            transport.fastForward();
      else if (data.equals("f07f7f0601f7"))
            transport.stop();
      else if (data.equals("f07f7f0602f7"))
            transport.play();
      else if (data.equals("f07f7f0606f7"))
            transport.record();
   }
}

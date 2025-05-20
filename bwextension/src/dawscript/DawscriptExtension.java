// SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
// SPDX-License-Identifier: MIT

package dawscript;

import java.io.File;

import com.bitwig.extension.api.util.midi.ShortMidiMessage;
import com.bitwig.extension.callback.ShortMidiMessageReceivedCallback;
import com.bitwig.extension.controller.api.ControllerHost;
import com.bitwig.extension.controller.ControllerExtension;
import py4j.GatewayServer;
import py4j.reflection.ReflectionUtil;
import py4j.reflection.RootClassLoadingStrategy;

import dawscript.BitwigExtensionLocator;
import dawscript.ControllerBridge;
import dawscript.PythonScript;

// file:///Applications/Bitwig%20Studio.app/Contents/Resources/Documentation/control-surface/api/com/bitwig/extension/package-summary.html

public class DawscriptExtension extends ControllerExtension
{
   private static final String EXTENSION_FILENAME = "dawscript.bwextension";
   private static final String PYTHON_SCRIPT_FILENAME = "dawscript.py";

   private GatewayServer gatewayServer;
   private PythonScript pythonScript;
   private ControllerBridge controller;

   protected DawscriptExtension(final DawscriptExtensionDefinition definition, final ControllerHost host)
   {
      super(definition, host);
   }

   @Override
   public void init()
   {
      // https://stackoverflow.com/questions/53288375/py4j-callback-interface-throws-invalid-interface-name-when-the-packaged-jar-i
      // https://github.com/py4j/py4j/issues/339#issuecomment-473655738
      ReflectionUtil.setClassLoadingStrategy(new RootClassLoadingStrategy());

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
         pythonScript.start(script);

         // TODO : detect script exec error (eg: syntax error)
      } catch (Exception e) {
         getHost().showPopupNotification(e.getMessage());
      }
   }

   @Override
   public void exit()
   {
      if (controller != null) {
         controller.on_script_stop();
      }

      pythonScript.stop();
      pythonScript = null;

      gatewayServer.shutdown();
      gatewayServer = null;
   }

   @Override
   public void flush()
   {
      // TODO : call controller.host_callback() with MIDI messages
   }

   public void setController(ControllerBridge controller)
   {
      this.controller = controller;

      controller.on_script_start();

      for (int i = 0; i < getExtensionDefinition().getNumMidiInPorts(); i++) {
         final int portIndex = i;
         getHost()
            .getMidiInPort(portIndex)
            .setMidiCallback((ShortMidiMessageReceivedCallback) msg -> onMidiCallback(portIndex, msg));
      }
   }

   private void onMidiCallback(int portIndex, ShortMidiMessage msg) 
   {
      // TODO : queue MIDI message
   }
}

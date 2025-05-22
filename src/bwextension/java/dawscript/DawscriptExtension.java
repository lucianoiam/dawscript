// SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
// SPDX-License-Identifier: MIT

package dawscript;

import java.io.File;
import java.util.ArrayList;
import java.util.Queue;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;

import com.bitwig.extension.api.util.midi.ShortMidiMessage;
import com.bitwig.extension.callback.ShortMidiMessageReceivedCallback;
import com.bitwig.extension.controller.api.Application;
import com.bitwig.extension.controller.api.ControllerHost;
import com.bitwig.extension.controller.api.TrackBank;
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
   private static final String BW_EXTENSION_FILENAME = "dawscript.bwextension";
   private static final String PYTHON_SCRIPT_FILENAME = "dawscript.py";

   private final Queue<ShortMidiMessage> midiQueue;
   private Application application;
   private GatewayServer gatewayServer;
   private PythonScript pythonScript;
   private ScheduledFuture startupCheck;
   private ControllerBridge controller;
   private String projectName;
   private TrackBank mainTrackBank;

   // https://stackoverflow.com/questions/53288375/py4j-callback-interface-throws-invalid-interface-name-when-the-packaged-jar-i
   // https://github.com/py4j/py4j/issues/339#issuecomment-473655738
   static
   {
      ReflectionUtil.setClassLoadingStrategy(new RootClassLoadingStrategy());
   }

   protected DawscriptExtension(final DawscriptExtensionDefinition definition, final ControllerHost host)
   {
      super(definition, host);
      midiQueue = new ConcurrentLinkedQueue<>();
   }

   @Override
   public void init()
   {
      final ControllerHost host = getHost();

      application = host.createApplication();

      try {
         gatewayServer = new GatewayServer(this);
         gatewayServer.start();

         pythonScript = new PythonScript(host::println, host::errorln);
         final File script = BitwigExtensionLocator.getPath(BW_EXTENSION_FILENAME)
            .toPath()
            .toRealPath()
            .getParent()
            .resolve(PYTHON_SCRIPT_FILENAME)
            .toFile();
         pythonScript.start(script);

         ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor();
         startupCheck = scheduler.schedule(() -> {
            if (controller == null) {
               host.showPopupNotification("Python script timeout, check BitwigStudio.log for errors."); 
            }
         }, 2, TimeUnit.SECONDS);
         scheduler.shutdown();

         application.projectName().addValueObserver(projectName -> {
            if (this.projectName != projectName) {
               this.projectName = projectName;
               if (controller != null) {
                  controller.on_project_load();
               }
            }
         });

         mainTrackBank = createMainTrackBank();
      } catch (Exception e) {
         host.showPopupNotification(e.getMessage());
      }
   }

   @Override
   public void exit()
   {
      if (startupCheck != null) {
         startupCheck.cancel(false);
         startupCheck = null;
      }

      if (controller != null) {
         controller.on_script_stop();
         controller = null;
      }

      if (pythonScript != null) {
         pythonScript.stop();
         pythonScript = null;
      }

      if (gatewayServer != null) {
         gatewayServer.shutdown();
         gatewayServer = null;
      }

      mainTrackBank = null;
      application = null;
   }

   @Override
   public void flush()
   {      
      if ((controller == null) || midiQueue.isEmpty()) {
         return;
      }

      final ArrayList<byte[]> messages = new ArrayList<>();
      ShortMidiMessage msg;

      while ((msg = midiQueue.poll()) != null) {
         messages.add(new byte[] {
            (byte) msg.getStatusByte(),
            (byte) msg.getData1(),
            (byte) msg.getData2()
         });
      }

      controller.host_callback(messages);
   }

   public void setController(ControllerBridge controller)
   {
      this.controller = controller;

      controller.on_script_start();
      controller.on_project_load();

      for (int i = 0; i < getExtensionDefinition().getNumMidiInPorts(); i++) {
         final int portIndex = i;
         getMidiInPort(portIndex).setMidiCallback((ShortMidiMessageReceivedCallback) msg -> {
             midiQueue.add(msg);
         });
      }
   }

   public TrackBank getMainTrackBank()
   {
      return mainTrackBank;
   }

   private TrackBank createMainTrackBank()
   {
      final TrackBank bank = getHost().getProject().getRootTrackGroup()
         .createMainTrackBank(128, 128, 128, true);

      bank.itemCount().addValueObserver(itemCount -> {
         if (controller != null) {
            controller.on_project_load();
         }
      });

      for (int i = 0; i < 128; i++) {
         bank.getItemAt(i).name().markInterested();
      }

      return bank;
   }
}

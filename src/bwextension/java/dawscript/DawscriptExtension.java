// SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
// SPDX-License-Identifier: MIT

package dawscript;

import java.io.File;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Queue;
import java.util.Timer;
import java.util.TimerTask;
import java.util.concurrent.ConcurrentLinkedQueue;

import com.bitwig.extension.api.util.midi.ShortMidiMessage;
import com.bitwig.extension.callback.ShortMidiMessageReceivedCallback;
import com.bitwig.extension.controller.api.Application;
import com.bitwig.extension.controller.api.ControllerHost;
import com.bitwig.extension.controller.api.Track;
import com.bitwig.extension.controller.api.TrackBank;
import com.bitwig.extension.controller.ControllerExtension;
import py4j.GatewayServer;
import py4j.reflection.ReflectionUtil;
import py4j.reflection.RootClassLoadingStrategy;

import dawscript.BitwigExtensionLocator;
import dawscript.Controller;
import dawscript.PythonRunnable;
import dawscript.PythonScript;

// file:///Applications/Bitwig%20Studio.app/Contents/Resources/Documentation/control-surface/api/com/bitwig/extension/package-summary.html

public class DawscriptExtension extends ControllerExtension
{
   public record Listener(long identifier, PythonRunnable runnable) {}

   private static final String BW_EXTENSION_FILENAME = "dawscript.bwextension";
   private static final String PYTHON_SCRIPT_FILENAME = "dawscript.py";

   private static final long HOST_CALLBACK_MS = 16;

   private final HashMap<String,ArrayList<Listener>> listeners;
   private final Queue<PythonRunnable> deferred;
   private final Queue<ShortMidiMessage> midiQueue;
   private Application application;
   private GatewayServer gatewayServer;
   private PythonScript pythonScript;
   private int hostCallbackCount;
   private Timer hostCallbackTimer;
   private Controller controller;
   private String projectName;
   private TrackBank projectTrackBank;

   // https://stackoverflow.com/questions/53288375/py4j-callback-interface-throws-invalid-interface-name-when-the-packaged-jar-i
   // https://github.com/py4j/py4j/issues/339#issuecomment-473655738
   static
   {
      ReflectionUtil.setClassLoadingStrategy(new RootClassLoadingStrategy());
   }

   protected DawscriptExtension(final DawscriptExtensionDefinition definition, final ControllerHost host)
   {
      super(definition, host);
      listeners = new HashMap<>();
      deferred = new ConcurrentLinkedQueue<>();
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

         application.projectName().addValueObserver(projectName -> {
            if (this.projectName != projectName) {
               this.projectName = projectName;
               if (controller != null) {
                  controller.on_project_load();
               }
            }
         });

         projectTrackBank = createProjectTrackBank();

         hostCallbackCount = 0;
         hostCallbackTimer = new Timer();
         hostCallbackTimer.scheduleAtFixedRate(new TimerTask() {
             @Override
             public void run() {
                 hostCallback();
             }
         }, 0, HOST_CALLBACK_MS);
      } catch (Exception e) {
         host.showPopupNotification(e.getMessage());
      }
   }

   @Override
   public void exit()
   {
      if (hostCallbackTimer != null) {
         hostCallbackTimer.cancel();
         hostCallbackTimer = null;
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

      projectTrackBank = null;
      application = null;
   }

   @Override
   public void flush()
   {
      // no-op
   }

   public void setController(Controller controller)
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

   public void addListener(Object target, String prop, long identifier, PythonRunnable runnable)
   {
      final String keyTargetProp = objectId(target) + "_" + prop;
      ArrayList<Listener> listenerList = listeners.get(keyTargetProp);

      if (listenerList == null) {
         listenerList = new ArrayList<>();
         listeners.put(keyTargetProp, listenerList);
      }

      listenerList.add(new Listener(identifier, runnable));
   }

   public void removeListener(Object target, String prop, long identifier)
   {
      final String keyTargetProp = objectId(target) + "_" + prop;
      final ArrayList<Listener> listenerList = listeners.get(keyTargetProp);

      if (listenerList == null) {
         return;
      }

      final Iterator<Listener> iterator = listenerList.iterator();
      while (iterator.hasNext()) {
          final Listener someListener = iterator.next();
          if (someListener.identifier == identifier) {
              iterator.remove();
          }
      }

      if (listenerList.isEmpty()) {
         listeners.remove(keyTargetProp);
      }
   }

   public TrackBank getProjectTrackBank()
   {
      return projectTrackBank;
   }

   private TrackBank createProjectTrackBank()
   {
      final TrackBank bank = getHost().getProject().getRootTrackGroup()
         .createMainTrackBank(128, 128, 128, true);

      bank.itemCount().addValueObserver(itemCount -> {
         if (controller != null) {
            controller.on_project_load();
         }
      });

      for (int i = 0; i < 128; i++) {
         final Track track = bank.getItemAt(i);
         
         track.name().markInterested();

         track.volume().value().addValueObserver(_0 -> {
            final String keyTargetProp = objectId(track) + "_volume";
            final ArrayList<Listener> listenerList = listeners.get(keyTargetProp);
            if (listenerList != null) {
               for (final Listener listener : listenerList) {
                  deferred.add(listener.runnable);
               }
            }
         });
      }

      return bank;
   }

   private void hostCallback()
   {
      hostCallbackCount++;

      if (controller == null) {
         if (hostCallbackCount == 100) {
            getHost().showPopupNotification("Python script timeout, check BitwigStudio.log for errors."); 
         }

         return;
      }

      if (! deferred.isEmpty()) {
         PythonRunnable runnable;

         while ((runnable = deferred.poll()) != null) {
            runnable.run();
         }
      }

      final ArrayList<byte[]> messages = new ArrayList<>();

      if (! midiQueue.isEmpty()) {
         ShortMidiMessage msg;

         while ((msg = midiQueue.poll()) != null) {
            messages.add(new byte[] {
               (byte) msg.getStatusByte(),
               (byte) msg.getData1(),
               (byte) msg.getData2()
            });
         }
      }

      controller.host_callback(messages);
   }

   private static String objectId(Object obj) {
      if (obj == null) return "null";
      return obj.getClass().getSimpleName() + "@" + Integer.toHexString(System.identityHashCode(obj));
   }
}

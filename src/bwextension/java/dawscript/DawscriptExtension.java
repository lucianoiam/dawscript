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
   private GatewayServer gatewayServer;
   private int pythonScriptWait;
   private PythonScript pythonScript;
   private TrackBank projectTrackBank;
   private Timer hostCallbackTimer;
   private String projectName;
   private Controller controller;

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
      final Application app = host.createApplication();

      try {
         gatewayServer = new GatewayServer(this);
         gatewayServer.start();

         pythonScriptWait = 0;
         pythonScript = new PythonScript(host::println, host::errorln);
         final File script = BitwigExtensionLocator.getPath(BW_EXTENSION_FILENAME)
            .toPath()
            .toRealPath()
            .getParent()
            .resolve(PYTHON_SCRIPT_FILENAME)
            .toFile();
         pythonScript.start(script);

         projectTrackBank = createProjectTrackBank();

         hostCallbackTimer = new Timer();
         hostCallbackTimer.scheduleAtFixedRate(new TimerTask() {
             @Override
             public void run() {
                 hostCallback();
             }
         }, 0, HOST_CALLBACK_MS);

         app.projectName().addValueObserver(projectName -> {
            if (this.projectName != projectName) {
               this.projectName = projectName;
               if (controller != null) {
                  try {
                     controller.on_project_load();
                  } catch (Exception e) {
                     e.printStackTrace();
                  }
               }
            }
         });
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
         try {
            controller.on_script_stop();
         } catch (Exception e) {
            e.printStackTrace();
         }
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
   }

   @Override
   public void flush()
   {
      // Empty
   }

   public void setController(Controller controller)
   {
      this.controller = controller;

      try {
         controller.on_script_start();
      } catch (Exception e) {
         e.printStackTrace();
      }

      try {
         controller.on_project_load();
      } catch (Exception e) {
         e.printStackTrace();
      }

      for (int i = 0; i < getExtensionDefinition().getNumMidiInPorts(); i++) {
         final int portIndex = i;
         getMidiInPort(portIndex).setMidiCallback((ShortMidiMessageReceivedCallback) msg -> {
             midiQueue.add(msg);
         });
      }
   }

   public void addListener(Object target, String prop, long identifier, PythonRunnable runnable)
   {
      final String key = keyTargetProp(target, prop);
      ArrayList<Listener> listenerList = listeners.get(key);

      if (listenerList == null) {
         listenerList = new ArrayList<>();
         listeners.put(key, listenerList);
      }

      listenerList.add(new Listener(identifier, runnable));
   }

   public void removeListener(Object target, String prop, long identifier)
   {
      final String key = keyTargetProp(target, prop);
      final ArrayList<Listener> listenerList = listeners.get(key);

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
         listeners.remove(key);
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
            try {
               controller.on_project_load();
            } catch (Exception e) {
               e.printStackTrace();
            }
         }
      });

      for (int i = 0; i < 128; i++) {
         final Track track = bank.getItemAt(i);
         
         track.trackType().markInterested();
         track.name().markInterested();

         track.mute().addValueObserver(_0 -> callListeners(track, "mute"));
         track.volume().value().addValueObserver(_0 -> callListeners(track, "volume"));
         track.pan().value().addValueObserver(_0 -> callListeners(track, "pan"));

         // TODO : call markInterested() on plugins and parameters
      }

      return bank;
   }

   private void callListeners(Object target, String prop)
   {
      final String key = keyTargetProp(target, prop);
      final ArrayList<Listener> listenerList = listeners.get(key);

      if (listenerList != null) {
         for (final Listener listener : listenerList) {
            deferred.add(listener.runnable);
         }
      }
   }

   private void hostCallback()
   {
      if (controller == null) {
         if (pythonScriptWait == 100) {
            pythonScriptWait = -1;
            getHost().showPopupNotification("Python script timeout, check Bitwig log file for errors."); 
         } else if (pythonScriptWait >= 0) {
            pythonScriptWait++;
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

      try {
         controller.host_callback(messages);
      } catch (Exception e) {
         // Empty
      }
   }

   private static String keyTargetProp(Object target, String prop)
   {
      return target.getClass().getSimpleName()
               + "@" + Integer.toHexString(System.identityHashCode(target))
               + "_" + prop;
   }
}

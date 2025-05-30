// SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
// SPDX-License-Identifier: MIT

package dawscript;

import java.io.File;
import java.io.IOException;
import java.net.BindException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Queue;
import java.util.Timer;
import java.util.TimerTask;
import java.util.concurrent.ConcurrentLinkedQueue;

import com.bitwig.extension.api.util.midi.ShortMidiMessage;
import com.bitwig.extension.callback.ShortMidiMessageReceivedCallback;
import com.bitwig.extension.controller.ControllerExtension;
import com.bitwig.extension.controller.ControllerExtensionDefinition;
import com.bitwig.extension.controller.api.Application;
import com.bitwig.extension.controller.api.ControllerHost;
import com.bitwig.extension.controller.api.Device;
import com.bitwig.extension.controller.api.DeviceBank;
import com.bitwig.extension.controller.api.Parameter;
import com.bitwig.extension.controller.api.ParameterBank;
import com.bitwig.extension.controller.api.Track;
import com.bitwig.extension.controller.api.TrackBank;
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

   private static final boolean ENABLE_PARAMETER_RANGE_UGLY_HACK = true;

   private static final int MAX_TRACKS = 64;
   private static final int MAX_DEVICES = 16;
   private static final int MAX_PARAMETERS = 32;

   private static final long HOST_CALLBACK_MS = 16;

   private final Queue<PythonRunnable> deferred;
   private final Queue<ShortMidiMessage> midiQueue;
   private final HashMap<String,ArrayList<Listener>> listeners;
   private final HashMap<Track,DeviceBank> deviceBanks;
   private final HashMap<Device,ParameterBank> parameterBanks;
   private TrackBank trackBank;
   private GatewayServer gatewayServer;
   private PythonScript pythonScript;
   private Timer hostCallbackTimer;
   private String projectName;
   private Controller controller;
   private int pythonScriptWait;
   private int parameterValueListenerPauseWait;

   // https://stackoverflow.com/questions/53288375/py4j-callback-interface-throws-invalid-interface-name-when-the-packaged-jar-i
   // https://github.com/py4j/py4j/issues/339#issuecomment-473655738
   static
   {
      ReflectionUtil.setClassLoadingStrategy(new RootClassLoadingStrategy());
   }

   public DawscriptExtension(final ControllerExtensionDefinition definition, final ControllerHost host)
   {
      super(definition, host);

      deferred = new ConcurrentLinkedQueue<>();
      midiQueue = new ConcurrentLinkedQueue<>();
      listeners = new HashMap<>();
      deviceBanks = new HashMap<>();
      parameterBanks = new HashMap<>();
   }

   @Override
   public void init()
   {
      final ControllerHost host = getHost();
      final String filename = pascalToSnake(getExtensionDefinition()
         .getClass().getSimpleName().replace("ExtensionDefinition", ""));

      try {
         startGatewayServer();

         pythonScriptWait = 0;
         pythonScript = new PythonScript(host::println, host::errorln);
         final File script = BitwigExtensionLocator.getPath(filename + ".bwextension")
            .toPath()
            .toRealPath()
            .getParent()
            .resolve(filename + ".py")
            .toFile();
         pythonScript.start(script, Integer.toString(gatewayServer.getPort()));

         initBanks();

         final Application app = host.createApplication();
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

   public TrackBank getTrackBank()
   {
      return trackBank;
   }

   public DeviceBank getTrackDeviceBank(Track track)
   {
      return deviceBanks.get(track);
   }

   public ParameterBank getPluginParameterBank(Device plugin)
   {
      return parameterBanks.get(plugin);
   }

   public double[] getParameterRange(Parameter parameter)
   {
      if (! ENABLE_PARAMETER_RANGE_UGLY_HACK) {
         return new double[] { 0.0, 1.0 };
      }

      parameterValueListenerPauseWait = 1;

      final double value = parameter.get();

      try {
         parameter.setImmediately(0.0);
         Thread.sleep(25);
      } catch (Exception e) {}
      final double lo = parameter.getRaw();

      try {
         parameter.setImmediately(1.0);
         Thread.sleep(25);
      } catch (Exception e) {}
      final double hi = parameter.getRaw();

      parameter.setImmediately(value);

      return new double[] { lo, hi };
   }

   private void startGatewayServer() throws Exception
   {
      int port = GatewayServer.DEFAULT_PORT;

      while (gatewayServer == null) {
         try {
            gatewayServer = new GatewayServer(this, port);
            gatewayServer.start();
         } catch (Exception e) {
            port++;
            if ((port - GatewayServer.DEFAULT_PORT) == 10) {
               throw e;
            }
         }
      }
   }

   private void initBanks()
   {
      trackBank = getHost().getProject().getRootTrackGroup()
         .createMainTrackBank(MAX_TRACKS, 0, 0, true);

      trackBank.itemCount().addValueObserver(itemCount -> {
         if (controller != null) {
            try {
               controller.on_project_load();
            } catch (Exception e) {
               e.printStackTrace();
            }
         }
      });

      for (int i = 0; i < MAX_TRACKS; i++) {
         final Track track = trackBank.getItemAt(i);
         track.trackType().markInterested();
         track.name().markInterested();
         track.mute().addValueObserver(_0 -> callListeners(track, "mute"));
         track.volume().value().addValueObserver(_0 -> callListeners(track, "volume"));
         track.pan().value().addValueObserver(_0 -> callListeners(track, "pan"));

         final DeviceBank deviceBank = track.createDeviceBank(MAX_DEVICES);
         deviceBank.itemCount().markInterested();
         deviceBanks.put(track, deviceBank);

         for (int j = 0; j < MAX_DEVICES; j++) {
            final Device device = deviceBank.getDevice(j);
            device.isPlugin().markInterested();
            device.name().markInterested();
            device.isEnabled().addValueObserver(_0 -> callListeners(device, "enabled"));

            final ParameterBank parameterBank = device.createCursorRemoteControlsPage(MAX_PARAMETERS);
            parameterBanks.put(device, parameterBank);

            for (int k = 0; k < MAX_PARAMETERS; k++) {
               final Parameter parameter = parameterBank.getParameter(k);
               parameter.name().markInterested();
               parameter.value().addRawValueObserver(_0 -> {
                  if (parameterValueListenerPauseWait == 0) {
                     callListeners(parameter, "value");
                  }
               });
            }
         }
      }
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

      if (parameterValueListenerPauseWait > 0) {
         parameterValueListenerPauseWait++;
         if (parameterValueListenerPauseWait == 10) {
            parameterValueListenerPauseWait = 0;
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

   private static String pascalToSnake(String input) {
      if (input == null || input.isEmpty()) {
         return input;
      }

      StringBuilder result = new StringBuilder();
      char[] chars = input.toCharArray();

      for (int i = 0; i < chars.length; i++) {
         char c = chars[i];
         if (Character.isUpperCase(c)) {
            if (i != 0) {
               result.append('_');
            }
            result.append(Character.toLowerCase(c));
         } else {
            result.append(c);
         }
      }

      return result.toString();
   }
}

// SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
// SPDX-License-Identifier: MIT

package dawscript;

import java.io.File;
import java.net.InetAddress;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Queue;
import java.util.Random;
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
import com.bitwig.extension.controller.api.SettableBooleanValue;
import com.bitwig.extension.controller.api.Track;
import com.bitwig.extension.controller.api.TrackBank;
import py4j.CallbackClient;
import py4j.GatewayServer;
import py4j.reflection.ReflectionUtil;
import py4j.reflection.RootClassLoadingStrategy;

// file:///Applications/Bitwig%20Studio.app/Contents/Resources/Documentation/control-surface/api/com/bitwig/extension/package-summary.html

public class DawscriptExtension extends ControllerExtension
{
   public record Listener(long identifier, PythonRunnable runnable) {}

   private static final boolean ENABLE_PARAMETER_RANGES_HACK = false;

   private static final int MAX_TRACKS = 64;
   private static final int MAX_DEVICES = 16;
   private static final int MAX_PARAMETERS = 32;

   private static final long HOST_CALLBACK_MS = 16;

   private final Queue<PythonRunnable> deferred;
   private final Queue<ShortMidiMessage> midiQueue;
   private final HashMap<String,ArrayList<Listener>> listeners;
   private final HashMap<Track,DeviceBank> deviceBanks;
   private final HashMap<Device,ParameterBank> parameterBanks;
   private HashMap<Parameter, double[]> parameterRanges;
   private SettableBooleanValue masterTrackMute;
   private TrackBank trackBank;
   private GatewayServer gatewayServer;
   private PythonScript pythonScript;
   private Timer hostCallbackTimer;
   private String projectName;
   private Controller controller;
   private int pythonScriptWaitTime;
   private int unmuteMasterTrackWaitTime;

   // https://stackoverflow.com/questions/53288375/py4j-callback-interface-throws-invalid-interface-name-when-the-packaged-jar-i
   // https://github.com/py4j/py4j/issues/339#issuecomment-473655738
   static
   {
      ReflectionUtil.setClassLoadingStrategy(new RootClassLoadingStrategy());
   }

   public static int getStableObjectId(Object handle)
   {
      return System.identityHashCode(handle);
   }

   // TODO: The Bitwig Java API appears to be asynchronous, so rapid, repeated
   // changes to the same parameter may not be reflected. The delay value below
   // works in most cases but should not be hardcoded. Consider tying it to a
   // dynamic value, such as the audio buffer size or some UI update interval.
   public static void callEngineAndWait(Runnable r)
   {
      try {
         r.run();
         Thread.sleep(25);
      } catch (Exception e) {}
   }

   public DawscriptExtension(final ControllerExtensionDefinition definition, final ControllerHost host)
   {
      super(definition, host);

      deferred = new ConcurrentLinkedQueue<>();
      midiQueue = new ConcurrentLinkedQueue<>();
      listeners = new HashMap<>();
      deviceBanks = new HashMap<>();
      parameterBanks = new HashMap<>();
      parameterRanges = new HashMap<>();
   }

   @Override
   public void init()
   {
      final ControllerHost host = getHost();
      final String filename = pascalToSnake(getExtensionDefinition()
         .getClass().getSimpleName().replace("ExtensionDefinition", ""));

      try {
         final int def_port = GatewayServer.DEFAULT_PORT;
         final int port = new Random().nextInt((65534 - def_port) + 1) + def_port;
         final CallbackClient callbackClient = new CallbackClient(port + 1,
            InetAddress.getByName("127.0.0.1"));
         gatewayServer = new GatewayServer.GatewayServerBuilder()
            .entryPoint(this)
            .javaPort(port)
            .callbackClient(callbackClient)
            .build();
         gatewayServer.start();

         pythonScriptWaitTime = 1;
         pythonScript = new PythonScript(host::println, host::errorln);
         final File script = BitwigExtensionLocator.getPath(filename + ".bwextension")
            .toPath()
            .toRealPath()
            .getParent()
            .resolve(filename + ".py")
            .toFile();
         pythonScript.start(script, Integer.toString(gatewayServer.getPort()));

         markInterested();

         final Application app = host.createApplication();
         app.projectName().addValueObserver(projectName -> {
            if (this.projectName != projectName) {
               this.projectName = projectName;
               if (controller != null) {
                  try {
                     //cacheParameterRanges();
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

   public double[] getParameterRange(Parameter param)
   {
      return parameterRanges.containsKey(param)
         ? parameterRanges.get(param)
         : new double[] { 0.0, 1.0 };
   }

   private void probeParameterRange(Parameter param)
   {
      final double[] range = new double[2];
      final double initValue = param.get();

      if (unmuteMasterTrackWaitTime > 0 || ! masterTrackMute.get()) {
         callEngineAndWait(() -> masterTrackMute.set(true));
         unmuteMasterTrackWaitTime = 1;
      }

      callEngineAndWait(() -> param.setImmediately(0.0));
      range[0] = param.getRaw();
      callEngineAndWait(() -> param.setImmediately(1.0));
      range[1] = param.getRaw();

      callEngineAndWait(() -> param.setImmediately(initValue));
      callListeners(param, "value");

      parameterRanges.put(param, range);
   }

   @SuppressWarnings("unused")
   private void markInterested()
   {
      masterTrackMute = getHost().createMasterTrack(0).mute();
      masterTrackMute.markInterested();

      trackBank = getHost().getProject().getRootTrackGroup()
         .createMainTrackBank(MAX_TRACKS, 0, 0, true);

      trackBank.itemCount().addValueObserver(arg -> {
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
         track.mute().addValueObserver(arg -> callListeners(track, "mute"));
         track.volume().value().addValueObserver(arg -> callListeners(track, "volume"));
         track.pan().value().addValueObserver(arg -> callListeners(track, "pan"));

         final DeviceBank deviceBank = track.createDeviceBank(MAX_DEVICES);
         deviceBank.itemCount().markInterested();
         deviceBanks.put(track, deviceBank);

         for (int j = 0; j < MAX_DEVICES; j++) {
            final Device device = deviceBank.getDevice(j);
            device.isPlugin().markInterested();
            device.name().markInterested();
            device.isEnabled().addValueObserver(arg -> callListeners(device, "enabled"));

            final ParameterBank parameterBank = device.createCursorRemoteControlsPage(MAX_PARAMETERS);
            parameterBanks.put(device, parameterBank);

            for (int k = 0; k < MAX_PARAMETERS; k++) {
               final Parameter parameter = parameterBank.getParameter(k);
               parameter.name().markInterested();
               parameter.value().addValueObserver(arg -> {
                  callListeners(parameter, "value");
               });
               parameter.displayedValue().addValueObserver(arg -> {
                  callListeners(parameter, "dpy_value");
               });
               if (ENABLE_PARAMETER_RANGES_HACK) {
                  parameter.exists().addValueObserver(arg -> {
                     deferred.add(() -> {
                        if (arg) {
                           probeParameterRange(parameter);
                        }
                     });
                  });
               }
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
         if (pythonScriptWaitTime > 0) {
            if (pythonScriptWaitTime++ == 100) {
               pythonScriptWaitTime = 0;
               getHost().showPopupNotification("Python script timeout, check Bitwig log file for errors."); 
            }
         }

         return;
      }

      if (unmuteMasterTrackWaitTime > 0) {
         if (unmuteMasterTrackWaitTime++ == 10) {
            unmuteMasterTrackWaitTime = 0;
            masterTrackMute.set(false);
         }
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
               + "@" + Integer.toHexString(getStableObjectId(target))
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

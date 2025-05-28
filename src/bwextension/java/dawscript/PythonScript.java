// SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
// SPDX-License-Identifier: MIT

package dawscript;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.File;
import java.util.Arrays;
import java.util.ArrayList;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;;

public class PythonScript
{
   private PrintLineFunction log, error;
   private Process process;
   private Thread readerThread;

   public PythonScript(PrintLineFunction log, PrintLineFunction error) {
      this.log = log;
      this.error = error;
   }

   public void start(File path, String... args) throws IOException {
      if (process != null) {
         throw new IOException("Python process already started");
      }

      ArrayList<String> command = new ArrayList<>();
      command.add(pythonPath());
      command.add(path.toString());
      command.addAll(Arrays.asList(args));

      final ProcessBuilder processBuilder = new ProcessBuilder(command);
      processBuilder.directory(path.getParentFile());

      process = processBuilder.start();
      process.getOutputStream().close();

      startReaderThread();
   }

   public void stop()
   {
      if (process != null) {
         process.destroy();

         try {
            if (! process.waitFor(1, TimeUnit.SECONDS)) {
               process.destroyForcibly();
            }
         } catch (InterruptedException e) {
            e.printStackTrace();
         }
      }

      process = null;

      stopReaderThread();
   }

   // macOS: tail -f $HOME/Library/Logs/Bitwig/BitwigStudio.log
   private void startReaderThread()
   {
      readerThread = new Thread(() -> {
         try (
            final BufferedReader stdout = new BufferedReader(new InputStreamReader(process.getInputStream()));
            final BufferedReader stderr = new BufferedReader(new InputStreamReader(process.getErrorStream()));
         ) {
            while (process != null || stdout.ready() || stderr.ready()) {
               while (stdout.ready()) {
                  final String line = stdout.readLine();
                  if (line != null) {
                     log.println(line);
                  }
               }
               while (stderr.ready()) {
                  final String line = stderr.readLine();
                  if (line != null) {
                     error.println(line);
                  }
               }
               Thread.sleep(10);
            }
         } catch (IOException | InterruptedException e) {
            e.printStackTrace();
         }
      });

      readerThread.start();
   }

   private void stopReaderThread()
   {
      if (readerThread != null) {
         try {
            readerThread.join();
         } catch (InterruptedException e) {
            e.printStackTrace();  
         }
      }

      readerThread = null;
   }

   private static String pythonPath() throws IOException
   {
      final String[][] commands = System.getProperty("os.name").toLowerCase().contains("win")
         ? new String[][] {
            {"where", "python3"},
            {"where", "python"}
         }
         : new String[][] {
            {"which", "python3"},
            {"which", "python"}
         };

      for (String[] cmd : commands) {
         try {
            final Process process = new ProcessBuilder(cmd).start();
            final BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            final String path = reader.readLine();

            process.waitFor();

            if (path != null && !path.isEmpty()) {
               return path.trim();
            }
         } catch (Exception ignored) {
            // continue
         }
      }

      throw new IOException("Could not find python3 executable");
   }

   @FunctionalInterface
   interface PrintLineFunction {
      void println(String s);
   }
}

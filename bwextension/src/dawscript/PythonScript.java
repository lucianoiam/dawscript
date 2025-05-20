// SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
// SPDX-License-Identifier: MIT

package dawscript;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.File;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

public class PythonScript
{
   private Process process;

   public void start(File path) throws IOException, InterruptedException, RuntimeException
   {
      if (process != null) {
         throw new RuntimeException("Python process already started");
      }

      final ProcessBuilder processBuilder = new ProcessBuilder(pythonPath(), path.toString());
      processBuilder.directory(path.getParentFile());
      processBuilder.redirectErrorStream(true);

      process = processBuilder.start();
   }

   public void stop() throws RuntimeException
   {
      if (process == null) {
         throw new RuntimeException("Python process not started");
      }

      process.destroy();

      try {
         if (! process.waitFor(1, TimeUnit.SECONDS)) {
            process.destroyForcibly();
         }
      } catch (InterruptedException e) {
         e.printStackTrace();
      }

      process = null;
   }

   private static String pythonPath() throws IOException, InterruptedException
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
}


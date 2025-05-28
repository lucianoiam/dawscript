// SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
// SPDX-License-Identifier: MIT

package dawscript;

import java.io.File;
import java.io.IOException;

public class BitwigExtensionLocator {
   private static final String[] PATH_LINUX = {
      System.getProperty("user.home") + "/Bitwig Studio/Extensions/",
      "/opt/bitwig-studio/resources/Extensions/"
   };

   private static final String[] PATH_MACOS = {
      System.getProperty("user.home") + "/Documents/Bitwig Studio/Extensions/",
      "/Applications/Bitwig Studio.app/Contents/Resources/Extensions/"
   };

   private static final String[] PATH_WINDOWS = {
      System.getProperty("user.home") + "\\Documents\\Bitwig Studio\\Extensions\\",
      "C:/Program Files/Bitwig Studio/Extensions/"
   };

   public static File getPath(String extensionName) throws IOException {
      final String os = System.getProperty("os.name").toLowerCase();
      final String[] paths;

      if (os.contains("linux")) {
         paths = PATH_LINUX;
      } else if (os.contains("mac")) {
         paths = PATH_MACOS;
      } else if (os.contains("win")) {
         paths = PATH_WINDOWS;
      } else {
         throw new IOException("Unsupported OS: " + os);
      }

      for (String path : paths) {
         final File extensionFile = searchInPath(path, extensionName);
         if (extensionFile != null) {
            return extensionFile;
         }
      }

      throw new IOException("Could not find extension: " + extensionName);
   }

   private static File searchInPath(String path, String extensionName) {
      final File directory = new File(path);

      if (directory.exists() && directory.isDirectory()) {
         final File extensionFile = new File(directory, extensionName);
         if (extensionFile.exists()) {
            return extensionFile;
         }
      }

      return null;
   }
}

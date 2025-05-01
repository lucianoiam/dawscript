#!/bin/sh

bwextension="../../dawscript.bwextension"
bwapi_version=22
bwapi_jar="extension-api-$bwapi_version.jar"
bwapi_jar_url="https://maven.bitwig.com/com/bitwig/extension-api/$bwapi_version/$bwapi_jar"
src="src/com/lucianoiam/*.java"

if ! command -v javac >/dev/null 2>&1; then
   echo "Error: 'javac' (Java compiler) not found."
   echo "Please install Java JDK 21 or newer from: https://www.java.com/"
   exit 1
fi

if [ ! -f "lib/$bwapi_jar" ]; then
   echo "Downloading Bitwig extension API JAR..."
   mkdir -p lib
   curl -L -o "lib/$bwapi_jar" "$bwapi_jar_url" || {
      echo "Failed to download $bwapi_jar_url"
      exit 1
   }
fi

echo "Compiling Java sources..."
javac --release 21 -d out -cp "lib/$bwapi_jar" $src || {
   echo "Compilation failed"
   exit 1
}

if [ -f "$bwextension" ]; then
   rm "$bwextension" || exit 1
fi

cd out || exit 1
zip -r "../$bwextension" . || exit 1
cd ..

echo "Build complete: $bwextension"

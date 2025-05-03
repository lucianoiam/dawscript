#!/bin/sh

bwextension="../../dawscript.bwextension"

bwapi_version="22"
bwapi_jar="extension-api-$bwapi_version.jar"
bwapi_jar_url="https://maven.bitwig.com/com/bitwig/extension-api/$bwapi_version/$bwapi_jar"

py4j_version="0.10.9.9"
py4j_jar="py4j-$py4j_version.jar"
py4j_jar_url="https://repo1.maven.org/maven2/net/sf/py4j/py4j/$py4j_version/$py4j_jar"

src="src/dawscript/*.java"

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

if [ ! -f "lib/$py4j_jar" ]; then
   echo "Downloading Py4J JAR..."
   mkdir -p lib
   curl -L -o "lib/$py4j_jar" "$py4j_jar_url" || {
      echo "Failed to download $py4j_jar_url"
      exit 1
   }
fi

echo "Compiling Java sources..."
javac --release 21 -d out -cp "lib/$bwapi_jar:lib/$py4j_jar" $src || {
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

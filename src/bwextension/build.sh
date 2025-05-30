#!/bin/bash

set -e
cwd="$(pwd)"

if [ $# -eq 0 ]; then
  bwext_path="../../../dawscript.bwextension"
  def_class_file=""
  def_class_name=""
elif [ $# -eq 3 ]; then
  bwext_path="$cwd/$1"
  def_class_file="$cwd/$2"
  def_class_name="$3"
else
  echo "Usage:"
  echo "  $0 <output> <def_class_file> <def_class_name>"
  exit 1
fi

bwapi_version="19"
bwapi_jar="extension-api-$bwapi_version.jar"
bwapi_jar_url="https://maven.bitwig.com/com/bitwig/extension-api/$bwapi_version/$bwapi_jar"

py4j_version="0.10.9.9"
py4j_jar="py4j-$py4j_version.jar"
py4j_jar_url="https://repo1.maven.org/maven2/net/sf/py4j/py4j/$py4j_version/$py4j_jar"

# Change to the script directory for relative lib/java paths
cd "$(dirname "${BASH_SOURCE[0]}")"

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

java_files=(
  BitwigExtensionLocator.java
  Controller.java
  DawscriptExtension.java
  DawscriptExtensionDefinition.java
  PythonRunnable.java
  PythonScript.java
)

if [ -n "$def_class_file" ]; then
  java_files=("${java_files[@]/DawscriptExtensionDefinition.java}")

  if [ -z "$def_class_name" ]; then
    echo "Error: If a definition .java file is provided, its class name must be specified."
    exit 1
  fi
else
  def_class_name="dawscript.DawscriptExtensionDefinition"
fi

java_src=()
for file in "${java_files[@]}"; do
  if [[ -n "$file" ]]; then
    java_src+=("java/dawscript/$file")
  fi
done

if [ -n "$def_class_file" ]; then
  if [ ! -f "$def_class_file" ]; then
    echo "Error: definition Java file '$def_class_file' does not exist."
    exit 1
  fi
  java_src+=("$def_class_file")
fi

echo "Compiling Java sources..."
javac --release 21 -d out/ -cp "lib/$bwapi_jar:lib/$py4j_jar" "${java_src[@]}" || {
   echo "Compilation failed"
   exit 1
}

echo "Copying files..."
mkdir -p out/META-INF/services
echo "$def_class_name" > out/META-INF/services/com.bitwig.extension.ExtensionDefinition

unzip -q -o "lib/$py4j_jar" "py4j/*" -d out || {
   echo "Copy files failed"
   exit 1
}

if [ -f "$bwext_path" ]; then
   rm "$bwext_path" || exit 1
fi

cd out || exit 1
zip -q -x "*.DS_Store" -r "$bwext_path" . || {
   echo "Compress failed"
   exit 1
}
cd ..

echo "Build complete: $bwext_path"

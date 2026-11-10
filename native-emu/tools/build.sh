#!/usr/bin/env bash
# P0 构建：JDK17 + Android SDK/NDK + Gradle 8.9
set -euo pipefail
cd "$(dirname "$0")/.."

export ANDROID_SDK_ROOT="${ANDROID_SDK_ROOT:-/root/android-sdk}"
export ANDROID_HOME="$ANDROID_SDK_ROOT"
export JAVA_HOME="${JAVA_HOME:-/usr/lib/jvm/java-17-openjdk-arm64}"

if [ ! -f third_party/mgba/CMakeLists.txt ]; then
  echo "缺少 mGBA 源码：third_party/mgba/"; exit 1
fi

GRADLE=${GRADLE:-gradle}
if [ -x ./gradlew ]; then GRADLE=./gradlew; fi

"$GRADLE" :app:assembleDebug "$@"
echo "APK: app/build/outputs/apk/debug/app-debug.apk"

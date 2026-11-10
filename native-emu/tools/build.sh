#!/usr/bin/env bash
# 本地（arm64/proot）构建：需要 qemu 包装的 aapt2 + 系统 cmake
# CI（x86_64）直接用 gradlew，不会走这些 hack
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

ARGS=()
# arm64 本机才需要这两个覆盖（CI 上 x86_64 原生工具链正常）
if [ -e /usr/bin/qemu-x86_64-static ]; then
  ARGS+=("-Pcmake.dir=/usr")
fi

"$GRADLE" :app:assembleDebug "${ARGS[@]}" "$@"
echo "APK: app/build/outputs/apk/debug/app-debug.apk"

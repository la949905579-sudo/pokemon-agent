#!/usr/bin/env bash
# P0 构建脚本：要求已安装 JDK17 + Android SDK + NDK r27
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f third_party/mgba/CMakeLists.txt ]; then
  echo "缺少 mGBA 源码：third_party/mgba/"; exit 1
fi

./gradlew :app:assembleDebug "$@"
echo "APK: app/build/outputs/apk/debug/app-debug.apk"

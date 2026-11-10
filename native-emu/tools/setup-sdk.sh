#!/usr/bin/env bash
# 安装 Android SDK 组件（JDK17 已由 apt 安装）
set -euo pipefail
SDK="${ANDROID_SDK_ROOT:-/root/android-sdk}"
export ANDROID_SDK_ROOT="$SDK"
export PATH="$SDK/cmdline-tools/latest/bin:$SDK/platform-tools:$PATH"

if [ ! -x "$SDK/cmdline-tools/latest/bin/sdkmanager" ]; then
  echo "先解压 commandline-tools 到 $SDK/cmdline-tools/latest"
  exit 1
fi

yes | sdkmanager --licenses >/dev/null
sdkmanager --install \
  "platform-tools" \
  "platforms;android-34" \
  "build-tools;34.0.0" \
  "ndk;27.0.12077973"

echo "SDK 就绪：$SDK"
echo "NDK: $(ls -d "$SDK"/ndk/* 2>/dev/null | tail -1)"

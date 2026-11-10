# native-emu（P0 骨架）

原生双屏 GBA 模拟器，规划见 `../NATIVE_EMU.md`。

## 结构
```
app/src/main/cpp/      JNI + mGBA 封装（emu_core）
app/src/main/java/     Kotlin（EmuCore 契约、MainActivity 双屏）
third_party/mgba/      需自行 clone（见 third_party/README.md）
tools/build.sh         构建脚本
```

## P0 顺序
1. `third_party/README.md` 拉 mGBA 源码
2. 装 JDK17 + Android SDK + NDK
3. `tools/build.sh` 编出 APK
4. 按 P0-1~P0-6 验收（见 NATIVE_EMU.md）

## 当前状态
- Gradle/CMake/JNI/Kotlin 骨架已就位
- `emu_core.cpp` 里的 mGBA 调用是 TODO 占位（等源码就位后按实际 API 填）
- 尚无工具链，未编译验证

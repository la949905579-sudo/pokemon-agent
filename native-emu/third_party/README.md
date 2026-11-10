# 第三方源码

## mGBA（必需）

```bash
cd native-emu/third_party
git clone --depth 1 --branch <稳定tag> https://github.com/mgba-emu/mgba.git
```

- 许可证：MPL 2.0（保留声明与源码获取方式）
- 源码就位后，`app/src/main/cpp/CMakeLists.txt` 才能编译
- P0 只编 arm64-v8a，关闭 Qt/SDL/GL/FFmpeg/PNG

## BIOS

- P0 不需要（mGBA 内置兜底）
- P1 在设置里让用户选择 `gba_bios.bin`

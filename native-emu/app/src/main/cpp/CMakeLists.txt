cmake_minimum_required(VERSION 3.22.1)
project(native-emu CXX C)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# mGBA 源码必须放在 native-emu/third_party/mgba/
set(MGBA_DIR ${CMAKE_CURRENT_LIST_DIR}/../../../../third_party/mgba)
if(NOT EXISTS ${MGBA_DIR}/CMakeLists.txt)
    message(FATAL_ERROR "缺少 mGBA 源码：请放到 native-emu/third_party/mgba/")
endif()

# mGBA 官方 CMake 会生成 mgba 库目标（P0 只开最小依赖）
set(BUILD_LIBRETRO OFF CACHE BOOL "" FORCE)
set(BUILD_QT OFF CACHE BOOL "" FORCE)
set(BUILD_SDL OFF CACHE BOOL "" FORCE)
set(BUILD_GL OFF CACHE BOOL "" FORCE)
set(BUILD_GLES2 OFF CACHE BOOL "" FORCE)
set(BUILD_FFMPEG OFF CACHE BOOL "" FORCE)
set(BUILD_PNG OFF CACHE BOOL "" FORCE)
set(BUILD_ZLIB ON CACHE BOOL "" FORCE)
add_subdirectory(${MGBA_DIR} mgba_build EXCLUDE_FROM_ALL)

add_library(emu SHARED
    emu_jni.cpp
    emu_core.cpp
)

target_include_directories(emu PRIVATE ${MGBA_DIR}/include)

# libretro 官方给 mGBA 用的是 DISABLE_THREADING（Android 上线程代理易崩）。
# 该宏会改变结构体布局，库和调用方必须一致定义。
# 对齐 libretro 官方 mgba 核心的编译定义（Android 上验证可用）
foreach(def DISABLE_THREADING MINIMAL_CORE=2 ENABLE_VFS)
    target_compile_definitions(mgba PRIVATE ${def})
    target_compile_definitions(emu PRIVATE ${def})
endforeach()

# 如果 mGBA 目标是 mgba（静态/共享），直接链；否则按需调整
target_link_libraries(emu PRIVATE mgba android log m)

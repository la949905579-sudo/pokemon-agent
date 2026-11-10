cmake_minimum_required(VERSION 3.22.1)
project(native-emu CXX C)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 给 mGBA 的 core init 插调试日志（崩在 core->init 时定位用）
set(EMU_ROOT ${CMAKE_CURRENT_LIST_DIR}/../../../..)
execute_process(COMMAND python3 ${EMU_ROOT}/tools/patch_mgba.py
                WORKING_DIRECTORY ${EMU_ROOT}
                RESULT_VARIABLE PATCH_RESULT
                OUTPUT_VARIABLE PATCH_OUT
                ERROR_VARIABLE PATCH_ERR)
message(STATUS "mgba patch: rc=${PATCH_RESULT} out=${PATCH_OUT} err=${PATCH_ERR}")

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
# libretro 官方给 mGBA 用的是 DISABLE_THREADING（Android 上线程代理易崩）。
# 该宏会改变结构体布局，库和调用方必须一致定义。
foreach(def DISABLE_THREADING ENABLE_VFS COLOR_16_BIT COLOR_5_6_5)
    target_compile_definitions(mgba PRIVATE ${def})
    target_compile_definitions(emu PRIVATE ${def})
endforeach()

# 如果 mGBA 目标是 mgba（静态/共享），直接链；否则按需调整
target_link_libraries(emu PRIVATE mgba android log m)

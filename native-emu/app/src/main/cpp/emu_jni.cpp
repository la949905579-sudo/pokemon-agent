#include <jni.h>
#include <android/log.h>
#include <cstring>
#include <vector>
#include "emu_core.h"

#define LOG_TAG "native-emu"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

static std::string jstr(JNIEnv* env, jstring s) {
    if (!s) return "";
    const char* c = env->GetStringUTFChars(s, nullptr);
    std::string out = c ? c : "";
    if (c) env->ReleaseStringUTFChars(s, c);
    return out;
}

extern "C" JNIEXPORT jboolean JNICALL
Java_com_dsh_emu_EmuCore_init(JNIEnv* env, jobject, jstring rom, jstring bios) {
    auto romS = jstr(env, rom);
    auto biosS = jstr(env, bios);
    bool ok = emu::Emu::get().init(romS.c_str(), biosS.empty() ? nullptr : biosS.c_str());
    LOGI("init ok=%d", ok);
    return ok ? JNI_TRUE : JNI_FALSE;
}

extern "C" JNIEXPORT jboolean JNICALL
Java_com_dsh_emu_EmuCore_start(JNIEnv*, jobject) {
    emu::Emu::get().start();
    return JNI_TRUE;
}

extern "C" JNIEXPORT void JNICALL
Java_com_dsh_emu_EmuCore_pause(JNIEnv*, jobject) { emu::Emu::get().pause(); }

extern "C" JNIEXPORT void JNICALL
Java_com_dsh_emu_EmuCore_resume(JNIEnv*, jobject) { emu::Emu::get().resume(); }

extern "C" JNIEXPORT void JNICALL
Java_com_dsh_emu_EmuCore_stop(JNIEnv*, jobject) { emu::Emu::get().stop(); }

extern "C" JNIEXPORT jlong JNICALL
Java_com_dsh_emu_EmuCore_runFrame(JNIEnv*, jobject) {
    return (jlong) emu::Emu::get().runFrame();
}

extern "C" JNIEXPORT void JNICALL
Java_com_dsh_emu_EmuCore_setKeys(JNIEnv*, jobject, jint mask) {
    emu::Emu::get().setKeys((uint32_t) mask);
}

extern "C" JNIEXPORT jbyteArray JNICALL
Java_com_dsh_emu_EmuCore_readMemory(JNIEnv* env, jobject, jint addr, jint len) {
    std::vector<uint8_t> buf((size_t) len);
    int n = emu::Emu::get().readMemory((uint32_t) addr, (uint32_t) len, buf.data());
    if (n <= 0) return nullptr;
    jbyteArray out = env->NewByteArray(n);
    env->SetByteArrayRegion(out, 0, n, (const jbyte*) buf.data());
    return out;
}

extern "C" JNIEXPORT jboolean JNICALL
Java_com_dsh_emu_EmuCore_writeMemory(JNIEnv* env, jobject, jint addr, jbyteArray data) {
    jsize len = env->GetArrayLength(data);
    std::vector<uint8_t> buf((size_t) len);
    env->GetByteArrayRegion(data, 0, len, (jbyte*) buf.data());
    return emu::Emu::get().writeMemory((uint32_t) addr, (uint32_t) len, buf.data())
        ? JNI_TRUE : JNI_FALSE;
}

extern "C" JNIEXPORT jlong JNICALL
Java_com_dsh_emu_EmuCore_frameCount(JNIEnv*, jobject) {
    return (jlong) emu::Emu::get().frameCount();
}

extern "C" JNIEXPORT void JNICALL
Java_com_dsh_emu_EmuCore_setSpeed(JNIEnv*, jobject, jint num, jint den) {
    emu::Emu::get().setSpeed((int) num, (int) den);
}

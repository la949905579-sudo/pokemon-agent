#include "emu_core.h"

#include <cstring>
#include <vector>
#include <fcntl.h>
#include <unistd.h>

static void nlog(const char* msg) {
    int fd = open("/sdcard/Download/emu_native.log", O_WRONLY | O_CREAT | O_APPEND, 0644);
    if (fd >= 0) {
        std::string line = std::string(msg) + "\n";
        write(fd, line.c_str(), line.size());
        close(fd);
    }
}

#include <mgba/core/core.h>
#include <mgba/core/config.h>
#include <mgba/core/version.h>
#include <mgba/gba/core.h>
#include <mgba-util/image.h>   // mColor

namespace emu {

Emu& Emu::get() {
    static Emu inst;
    return inst;
}

bool Emu::init(const char* rom_path, const char* bios_path) {
    std::lock_guard<std::mutex> lk(mu_);
    if (core_) return true;
    if (!rom_path || !*rom_path) return false;

    // mGBA 要求先初始化全局配置系统，否则后续调用会崩
    nlog("init: config");
    config_ = new struct mCoreConfig{};
    mCoreConfigInit(config_, "native-emu");

    nlog("init: create core");
    core_ = mCoreCreate(mPLATFORM_GBA);
    if (!core_) { nlog("init: core null"); return false; }
    // 先应用配置，再初始化 core
    mCoreInitConfig(core_, nullptr);
    nlog("init: core init");
    if (!core_->init(core_)) { nlog("init: core init failed"); return false; }
    nlog("init: core ready");

    // 顺序：先 loadROM（会创建视频上下文），再 setVideoBuffer，最后 reset
    nlog("init: load file");
    if (!mCoreLoadFile(core_, rom_path)) {
        nlog("init: load failed");
        return false;
    }
    nlog("init: load ok");

    nlog("init: video buffer");
    video_.assign(VIDEO_W * VIDEO_H, 0);
    core_->setVideoBuffer(core_, (mColor*) video_.data(), VIDEO_W);
    nlog("init: buffer ok");
    (void) bios_path;

    nlog("init: reset");
    core_->reset(core_);
    nlog("init: done");
    return true;
}

void Emu::start() { std::lock_guard<std::mutex> lk(mu_); running_ = true; }
void Emu::pause() { std::lock_guard<std::mutex> lk(mu_); running_ = false; }
void Emu::resume() { std::lock_guard<std::mutex> lk(mu_); running_ = true; }

void Emu::stop() {
    std::lock_guard<std::mutex> lk(mu_);
    running_ = false;
    if (core_) {
        core_->deinit(core_);
        core_ = nullptr;
    }
    if (config_) {
        mCoreConfigDeinit(config_);
        delete config_;
        config_ = nullptr;
    }
}

uint64_t Emu::runFrame() {
    std::lock_guard<std::mutex> lk(mu_);
    if (!running_ || !core_) return frames_;
    core_->runFrame(core_);
    frames_++;
    return frames_;
}

void Emu::setKeys(uint32_t mask) {
    std::lock_guard<std::mutex> lk(mu_);
    if (core_) core_->setKeys(core_, mask);
}

int Emu::readMemory(uint32_t addr, uint32_t len, uint8_t* out) {
    std::lock_guard<std::mutex> lk(mu_);
    if (!core_ || !out) return 0;
    for (uint32_t i = 0; i < len; i++) {
        out[i] = (uint8_t) core_->rawRead8(core_, addr + i, 0);
    }
    return (int) len;
}

bool Emu::writeMemory(uint32_t addr, uint32_t len, const uint8_t* data) {
    std::lock_guard<std::mutex> lk(mu_);
    if (!core_ || !data) return false;
    for (uint32_t i = 0; i < len; i++) {
        core_->rawWrite8(core_, addr + i, 0, data[i]);
    }
    return true;
}

const uint32_t* Emu::videoBuffer() {
    return video_.data();
}

int Emu::videoWidth() { return VIDEO_W; }
int Emu::videoHeight() { return VIDEO_H; }

uint64_t Emu::frameCount() {
    std::lock_guard<std::mutex> lk(mu_);
    return frames_;
}

void Emu::setSpeed(int num, int den) {
    std::lock_guard<std::mutex> lk(mu_);
    speed_num_ = num > 0 ? num : 1;
    speed_den_ = den > 0 ? den : 1;
}

} // namespace emu

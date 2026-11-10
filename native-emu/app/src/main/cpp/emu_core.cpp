#include "emu_core.h"

// mGBA 头文件（以 third_party/mgba/include 为准）
#include <mgba/core/core.h>
#include <mgba/core/version.h>
#include <mgba/gba/core.h>

namespace emu {

Emu& Emu::get() {
    static Emu inst;
    return inst;
}

bool Emu::init(const char* rom_path, const char* bios_path) {
    std::lock_guard<std::mutex> lk(mu_);
    // TODO(P0-2): 按 mGBA 实际 API 调整：
    //   core_ = mCoreCreate(mPLATFORM_GBA);
    //   mCoreLoadFile(core_, rom_path);
    //   if (bios_path) core_->loadBIOS(core_, bios_path, false);
    //   mCoreInitConfig(core_, nullptr);
    //   core_->reset(core_);
    // 目前源码未就位，先返回 false 占位
    (void) rom_path;
    (void) bios_path;
    return false;
}

void Emu::start() {
    std::lock_guard<std::mutex> lk(mu_);
    running_ = true;
}

void Emu::pause() {
    std::lock_guard<std::mutex> lk(mu_);
    running_ = false;
}

void Emu::resume() {
    std::lock_guard<std::mutex> lk(mu_);
    running_ = true;
}

void Emu::stop() {
    std::lock_guard<std::mutex> lk(mu_);
    running_ = false;
    if (core_) {
        // TODO(P0): core_->deinit(core_); core_ = nullptr;
    }
}

uint64_t Emu::runFrame() {
    // TODO(P0-3): core_->runFrame(core_) 并取帧缓冲
    std::lock_guard<std::mutex> lk(mu_);
    if (!running_) return frames_;
    frames_++;
    return frames_;
}

void Emu::setKeys(uint32_t mask) {
    // TODO(P0-4): core_->setKeys(core_, mask)
    (void) mask;
}

int Emu::readMemory(uint32_t addr, uint32_t len, uint8_t* out) {
    std::lock_guard<std::mutex> lk(mu_);
    if (!core_) return 0;
    // TODO: core_->readMemory(core_, addr, len, out)
    (void) addr; (void) len; (void) out;
    return 0;
}

bool Emu::writeMemory(uint32_t addr, uint32_t len, const uint8_t* data) {
    std::lock_guard<std::mutex> lk(mu_);
    if (!core_) return false;
    // TODO: core_->writeMemory(core_, addr, len, data)
    (void) addr; (void) len; (void) data;
    return false;
}

const uint32_t* Emu::videoBuffer() {
    // TODO: core_->videoBuffer / mCoreGetVideoBuffer
    return nullptr;
}

int Emu::videoWidth() { return 240; }
int Emu::videoHeight() { return 160; }

uint64_t Emu::frameCount() {
    std::lock_guard<std::mutex> lk(mu_);
    return frames_;
}

void Emu::setSpeed(int num, int den) {
    std::lock_guard<std::mutex> lk(mu_);
    speed_num_ = num;
    speed_den_ = den;
}

} // namespace emu

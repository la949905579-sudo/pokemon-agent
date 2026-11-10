#include "emu_core.h"

#include <cstring>
#include <vector>
#include <fcntl.h>

#include <mgba/core/core.h>
#include <mgba/core/config.h>
#include <mgba/core/version.h>
#include <mgba/gba/core.h>
#include <mgba-util/image.h>   // mColor
#include <mgba-util/vfs.h>

namespace emu {

Emu& Emu::get() {
    static Emu inst;
    return inst;
}

bool Emu::init(const char* rom_path, const char* bios_path) {
    std::lock_guard<std::mutex> lk(mu_);
    if (core_) return true;
    if (!rom_path || !*rom_path) return false;

    core_ = mCoreCreate(mPLATFORM_GBA);
    if (!core_) return false;
    mCoreInitConfig(core_, nullptr);

    video_.assign(VIDEO_W * VIDEO_H, 0);
    core_->setVideoBuffer(core_, (mColor*) video_.data(), VIDEO_W);

    struct VFile* vf = VFileOpen(rom_path, O_RDONLY);
    if (!vf) return false;
    bool ok = core_->loadROM(core_, vf);
    if (!ok) {
        vf->close(vf);
        return false;
    }

    if (bios_path && *bios_path) {
        struct VFile* bvf = VFileOpen(bios_path, O_RDONLY);
        if (bvf) {
            core_->loadBIOS(core_, bvf, 0);
        }
    }

    core_->reset(core_);
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

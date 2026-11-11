#include "emu_core.h"

#include <cstring>
#include <cstdio>
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
#include <mgba-util/image.h>
#include <mgba-util/vfs.h>   // mColor

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

    nlog("init: find core");
    // 与 libretro 前端一致：按 ROM 头自动识别平台
    // 清理上一次失败的 core（否则下次会误判“已初始化”）
    if (core_) { core_ = nullptr; }
    core_ = mCoreFind(rom_path);
    if (!core_) { nlog("init: core null"); return false; }
    if (!core_->init || !core_->runFrame) {
        nlog("init: core invalid -> reset");
        core_ = nullptr;
        return false;
    }
    mCoreInitConfig(core_, nullptr);
    { char b[160]; snprintf(b, sizeof(b), "init: core=%p init=%p runFrame=%p platform=%p",
        (void*)core_, (void*)core_->init, (void*)core_->runFrame, (void*)core_->platform); nlog(b); }
    if (!core_->init) { nlog("init: abort null init"); return false; }
    if (!core_->init(core_)) { nlog("init: core init failed"); return false; }
    nlog("init: core ready");

    // 没有 BIOS 时必须跳过 BIOS 引导，直接从 ROM 入口执行（否则 CPU 从空 BIOS 区跑会崩）
    nlog("init: skip bios");
    core_->opts.skipBios = true;
    core_->opts.useBios = false;

    { char b[80]; snprintf(b, sizeof(b), "init: bytesPerPixel=%d sizeof(mColor)=%zu",
        BYTES_PER_PIXEL, sizeof(mColor)); nlog(b); }
    nlog("init: video buffer");
    video_.assign(VIDEO_W * VIDEO_H, 0);
    core_->setVideoBuffer(core_, (mColor*) video_.data(), VIDEO_W);
    nlog("init: buffer ok");

    // 顺序与 libretro 一致：init -> setVideoBuffer -> loadROM -> reset
    nlog("init: load file");
    if (!mCoreLoadFile(core_, rom_path)) {
        nlog("init: load failed");
        return false;
    }
    nlog("init: load ok");
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
    bool first = (frames_ == 0);
    if (first) {
        char b[200];
        size_t rs = core_->romSize(core_);
        snprintf(b, sizeof(b), "frame: cpu=%p board=%p romSize=%zu", 
                 (void*)core_->cpu, (void*)core_->board, rs);
        nlog(b);
    }
    core_->runFrame(core_);
    if (first) nlog("frame: first after");
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

bool Emu::saveState(const char* path) {
    std::lock_guard<std::mutex> lk(mu_);
    nlog("save: begin");
    if (!core_) { nlog("save: no core"); return false; }
    if (!core_->saveState) { nlog("save: no api"); return false; }
    size_t sz = core_->stateSize ? core_->stateSize(core_) : 0;
    { char b[64]; snprintf(b, sizeof(b), "save: stateSize=%zu", sz); nlog(b); }
    struct VFile* vf = VFileOpen(path, O_WRONLY | O_CREAT | O_TRUNC);
    if (!vf) { nlog("save: vfile fail"); return false; }
    nlog("save: writing");
    bool ok = core_->saveState(core_, vf);
    nlog(ok ? "save: ok" : "save: failed");
    vf->close(vf);
    return ok;
}

bool Emu::loadState(const char* path) {
    std::lock_guard<std::mutex> lk(mu_);
    if (!core_ || !core_->loadState) return false;
    struct VFile* vf = VFileOpen(path, O_RDONLY);
    if (!vf) return false;
    bool ok = core_->loadState(core_, vf);
    vf->close(vf);
    return ok;
}

void Emu::setSpeed(int num, int den) {
    std::lock_guard<std::mutex> lk(mu_);
    speed_num_ = num > 0 ? num : 1;
    speed_den_ = den > 0 ? den : 1;
}

} // namespace emu

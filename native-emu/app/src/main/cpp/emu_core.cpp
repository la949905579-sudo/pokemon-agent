#include "emu_core.h"

#include <cstring>
#include <cstdio>
#include <ctime>
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

// 结构化日志（格式见 docs/OBSERVABILITY.md）：ISO8601 时间 + 级别 + 事件名 + key=value
static void nlogEv(const char* level, const char* event, const char* fields) {
    char ts[32] = "1970-01-01T00:00:00Z";
    time_t now = time(nullptr);
    struct tm tmv;
    if (gmtime_r(&now, &tmv)) {
        strftime(ts, sizeof(ts), "%Y-%m-%dT%H:%M:%SZ", &tmv);
    }
    char line[512];
    snprintf(line, sizeof(line), "%s %-5s %s %s", ts, level, event, fields);
    nlog(line);
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
    if (!rom_path || !*rom_path) return false;
    // 允许重新加载 ROM：先释放旧的 core
    if (core_) {
        nlog("init: deinit old core");
        core_->deinit(core_);
        core_ = nullptr;
    }

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

    // 电池存档（游戏内存档）：mGBA 前端必须显式挂 .sav 文件，否则存档只留在内存里，
    // 关掉 App 就丢。落点与桌面 mGBA 默认一致：<ROM 目录>/<ROM 名>.sav。
    // 必须在 mCoreLoadFile 之后调用（依赖它设好的 core->dirs / baseName）。
    if (mCoreAutoloadSave(core_)) {
        nlogEv("INFO", "emu.save", "stage=autoload ok=true");
    } else {
        // 存档文件打不开/目录不可写：不阻断启动，只降级为「存档不落盘」
        nlogEv("WARN", "emu.save", "stage=autoload ok=false code=open_failed");
    }

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

int Emu::bytesPerPixel() {
    return BYTES_PER_PIXEL;
}

bool Emu::saveState(const char* path) {
    std::lock_guard<std::mutex> lk(mu_);
    nlog("save: begin");
    if (!core_) { nlog("save: no core"); return false; }
    if (!core_->saveState) { nlog("save: no api"); return false; }
    size_t sz = core_->stateSize ? core_->stateSize(core_) : 0;
    { char b[64]; snprintf(b, sizeof(b), "save: stateSize=%zu", sz); nlog(b); }
    nlog("save: writing");
    // 自己写文件：core->saveState 接受内存缓冲区
    std::vector<uint8_t> buf(sz);
    if (!core_->saveState) { nlog("save: no state api"); return false; }
    bool ok = core_->saveState(core_, buf.data());
    if (!ok) { nlog("save: serialize failed"); return false; }
    FILE* f = fopen(path, "wb");
    if (!f) { nlog("save: fopen failed"); return false; }
    size_t wrote = fwrite(buf.data(), 1, sz, f);
    fclose(f);
    { char b[80]; snprintf(b, sizeof(b), "save: wrote %zu/%zu", wrote, sz); nlog(b); }
    return wrote == sz;
}

bool Emu::loadState(const char* path) {
    std::lock_guard<std::mutex> lk(mu_);
    if (!core_ || !core_->loadState) return false;
    FILE* f = fopen(path, "rb");
    if (!f) { nlog("load: fopen failed"); return false; }
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    if (sz <= 0) { fclose(f); return false; }
    std::vector<uint8_t> buf((size_t) sz);
    size_t rd = fread(buf.data(), 1, (size_t) sz, f);
    fclose(f);
    if (rd != (size_t) sz) return false;
    if (!core_->loadState) return false;
    bool ok = core_->loadState(core_, buf.data());
    nlog(ok ? "load: ok" : "load: failed");
    return ok;
}

void Emu::setSpeed(int num, int den) {
    std::lock_guard<std::mutex> lk(mu_);
    speed_num_ = num > 0 ? num : 1;
    speed_den_ = den > 0 ? den : 1;
}

} // namespace emu

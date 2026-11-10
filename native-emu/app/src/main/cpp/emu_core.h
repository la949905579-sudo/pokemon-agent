#pragma once
#include <cstdint>
#include <mutex>
#include <vector>

struct mCore;

namespace emu {

/// 单例封装：mGBA core + 输入/内存/存档/速度控制。
/// P0 只实现 init/runFrame/setKeys/read/write；存档与速度先占位。
class Emu {
public:
    static Emu& get();

    bool init(const char* rom_path, const char* bios_path);
    void start();
    void pause();
    void resume();
    void stop();

    /// 跑一帧；返回帧号（P0 用计数器）
    uint64_t runFrame();

    /// 按键位掩码（见 EmuCore.kt 注释）
    void setKeys(uint32_t mask);

    int readMemory(uint32_t addr, uint32_t len, uint8_t* out);
    bool writeMemory(uint32_t addr, uint32_t len, const uint8_t* data);

    /// 颜色帧缓冲（P0：240x160 ARGB8888）
    const uint32_t* videoBuffer();
    int videoWidth();
    int videoHeight();

    uint64_t frameCount();
    void setSpeed(int num, int den);

    static constexpr int VIDEO_W = 240;
    static constexpr int VIDEO_H = 160;

private:
    Emu() = default;
    mCore* core_ = nullptr;
    std::mutex mu_;
    uint64_t frames_ = 0;
    std::vector<uint32_t> video_;
    bool running_ = false;
    int speed_num_ = 1, speed_den_ = 1;
};

} // namespace emu

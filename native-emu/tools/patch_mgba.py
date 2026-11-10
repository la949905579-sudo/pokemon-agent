#!/usr/bin/env python3
"""CI 用：给 mGBA 的 _GBACoreInit 插调试日志（崩在 core->init 时定位用）。"""
import sys

p = sys.argv[1] if len(sys.argv) > 1 else "third_party/mgba/src/gba/core.c"
s = open(p).read()

dbg = (
    '#include <fcntl.h>\n'
    '#include <unistd.h>\n'
    '#include <string.h>\n'
    'static void dbg(const char* m) {\n'
    '    int fd = open("/sdcard/Download/mgba_init.log", O_WRONLY | O_CREAT | O_APPEND, 0644);\n'
    '    if (fd >= 0) { write(fd, m, strlen(m)); write(fd, "\\n", 1); close(fd); }\n'
    '}\n'
)

if 'static void dbg(' not in s:
    s = s.replace('static bool _GBACoreInit(struct mCore* core) {',
                  dbg + 'static bool _GBACoreInit(struct mCore* core) {', 1)

pairs = [
    ('GBACreate(gba);', 'dbg("1 GBACreate"); GBACreate(gba); dbg("1b GBACreate ok");'),
    ('ARMInit(cpu);', 'dbg("2 ARMInit"); ARMInit(cpu); dbg("2b ARMInit ok");'),
    ('GBAVideoDummyRendererCreate(&gbacore->dummyRenderer);',
     'dbg("3 DummyRenderer"); GBAVideoDummyRendererCreate(&gbacore->dummyRenderer); dbg("3b dummy ok");'),
    ('GBAVideoSoftwareRendererCreate(&gbacore->renderer);',
     'dbg("4 SoftwareRenderer"); GBAVideoSoftwareRendererCreate(&gbacore->renderer); dbg("4b sw ok");'),
]
for old, new in pairs:
    if old in s and new not in s:
        s = s.replace(old, new, 1)

# 函数末尾 return true 前打点（只替换 _GBACoreInit 里的第一个）
idx = s.find('static bool _GBACoreInit')
if idx >= 0:
    ret = s.find('return true;', idx)
    if ret >= 0 and 'dbg("5 init done")' not in s:
        s = s[:ret] + 'dbg("5 init done"); ' + s[ret:]

open(p, 'w').write(s)
print("patched mGBA debug logging")

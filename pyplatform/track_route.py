"""后台记录用户操作时的坐标轨迹（带地图 ID，能分辨换图）。"""
import time, sys, struct
sys.path.insert(0, '/workspace' if False else '/root/workspace')
from state import rd

def read_pos():
    d = rd(0x02036e48, 4, retries=1)
    if not d or len(d) != 4:
        return None
    return struct.unpack_from('<hh', d, 0)

def read_map():
    d = rd(0x02036DFC, 4, retries=1)
    if not d or len(d) != 4:
        return None
    return struct.unpack_from('<I', d, 0)[0]

last = None
with open('/root/workspace/route_log.txt', 'w') as f:
    t0 = time.time()
    while time.time() - t0 < 300:
        p = read_pos()
        m = read_map()
        if p:
            key = (p[0], p[1], m)
            if key != last:
                f.write(f'{time.time()-t0:6.1f}s  x={p[0]:3d} y={p[1]:3d}  map={hex(m) if m else "?"}\n')
                f.flush()
                last = key
        time.sleep(0.25)
    f.write('END\n')
print('tracker done')

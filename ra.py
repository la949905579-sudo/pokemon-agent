import socket, struct, time, sys, signal, atexit
PORT=55400
IDS={"b":0,"y":1,"select":2,"start":3,"up":4,"down":5,"left":6,"right":7,
     "a":8,"x":9,"l":10,"r":11,"l2":12,"r2":13,"l3":14,"r3":15}
s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
def msg(bid,state):
    return struct.pack("<iiiih",0,1,0,bid,state)+b"\x00\x00"
def send(bid,state):
    s.sendto(msg(bid,state),("127.0.0.1",PORT))

def release_all():
    """松开所有键。被 timeout/中断杀掉时也必须执行，否则角色会一直走。"""
    for bid in range(16):
        try:
            send(bid, 0)
        except Exception:
            pass

def press(name,dur=0.35):
    bid=IDS[name]
    try:
        send(bid,1); time.sleep(dur)
    finally:
        send(bid,0)
    time.sleep(0.15)

atexit.register(release_all)
def _term(sig, frm):
    release_all()
    sys.exit(0)
try:
    signal.signal(signal.SIGTERM, _term)
    signal.signal(signal.SIGINT, _term)
except (ValueError, RuntimeError):
    pass  # 非主线程无法注册信号，忽略

if __name__=="__main__":
    for step in sys.argv[1:]:
        parts=step.split(":")
        press(parts[0], float(parts[1]) if len(parts)>1 else 0.35)

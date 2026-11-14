"""离线测试：统一日志 JSONL 格式 + logq 过滤。"""
import json
import os
import sys
import tempfile
from argparse import Namespace
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pyplatform"))
import log
import logq


def test_jsonl_fields():
    d = tempfile.mkdtemp()
    with patch.object(log, "LOG_DIR", d), \
         patch.object(log, "_fp", {"day": None, "fh": None}):
        log.info("test", "evt", a=1, b={"x": 2})
        log.error("test", "bad", why="x")
        log._fp["fh"].close()
    files = os.listdir(d)
    assert len(files) == 1, files
    recs = [json.loads(line) for line in open(os.path.join(d, files[0]), encoding="utf-8")]
    assert recs[0]["mod"] == "test" and recs[0]["data"]["a"] == 1, recs[0]
    assert recs[1]["level"] == "error", recs[1]
    assert recs[0]["session"] and recs[0]["ts"], recs[0]
    print("A JSONL 字段 ok")


def ns(**kw):
    d = dict(mod=None, event=None, level=None, since=None, grep=None)
    d.update(kw)
    return Namespace(**d)


def test_logq_filter():
    rows = [{"mod": "a", "event": "x", "data": {"k": 1}},
            {"mod": "b", "event": "y", "data": {}}]
    assert logq.match(rows[0], ns(mod="a"))
    assert not logq.match(rows[0], ns(mod="b"))
    assert logq.match(rows[1], ns(grep="y"))
    assert not logq.match(rows[1], ns(event="x"))
    print("B logq 过滤 ok")


test_jsonl_fields()
test_logq_filter()
print("全部通过")

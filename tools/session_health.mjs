#!/usr/bin/env node
/**
 * 会话健康检查：给交接提供客观触发依据。
 *
 * 用法：
 *   node tools/session_health.mjs                 # 检查最近活动的会话
 *   node tools/session_health.mjs <session-uuid>  # 指定会话
 *   node tools/session_health.mjs --json          # 机器可读
 *
 * 退出码：0 = 健康；1 = 命中交接阈值（应当交接）。
 *
 * 阈值来自 docs/HANDOVER.md：
 *   - 轮次 > 100
 *   - 上下文压缩 ≥ 2 次
 *   - 最近连续 2 轮是「空回合」（无正文、无工具调用）
 */
import fs from "node:fs";
import path from "node:path";
import zlib from "node:zlib";

const ROOT = "/root/.dsh/sessions";
const TURN_LIMIT = 100;
const COMPACT_LIMIT = 2;
const EMPTY_STREAK_LIMIT = 2;

function newestSession(root) {
  const dirs = [];
  for (const proj of fs.readdirSync(root)) {
    const p = path.join(root, proj);
    if (!fs.statSync(p).isDirectory()) continue;
    for (const s of fs.readdirSync(p)) {
      if (!s.startsWith("session-")) continue;
      const log = path.join(p, s, "session.v4.jsonl.zstd");
      if (fs.existsSync(log)) dirs.push({ id: s.replace("session-", ""), log, mtime: fs.statSync(log).mtimeMs });
    }
  }
  dirs.sort((a, b) => b.mtime - a.mtime);
  return dirs[0];
}

function readEvents(logPath) {
  const buf = zlib.zstdDecompressSync(fs.readFileSync(logPath)).toString("utf8");
  const out = [];
  for (const line of buf.split("\n")) {
    if (!line.startsWith("{")) continue;
    try { out.push(JSON.parse(line)); } catch { /* 跳过坏行 */ }
  }
  return out;
}

function analyse(events) {
  let turns = 0, compactions = 0;
  const perTurn = new Map(); // turn -> {text, call}
  for (const e of events) {
    if (e.type === "turn/start") turns++;
    if (e.type === "compaction/end") compactions++;
    if (e.type === "assistant/message") {
      const d = e.data || {};
      const c = (d.message && d.message.content) || [];
      const text = c.filter(p => p.type === "text").map(p => p.text).join("").trim();
      const call = c.some(p => p.type === "tool-call");
      if (typeof d.turn === "number") {
        const cur = perTurn.get(d.turn) || { text: false, call: false };
        perTurn.set(d.turn, { text: cur.text || !!text, call: cur.call || call });
      }
    }
  }
  const ordered = [...perTurn.keys()].sort((a, b) => a - b);
  const emptyTurns = ordered.filter(t => { const v = perTurn.get(t); return !v.text && !v.call; });
  let streak = 0;
  for (let i = ordered.length - 1; i >= 0; i--) {
    const v = perTurn.get(ordered[i]);
    if (!v.text && !v.call) streak++; else break;
  }
  return { turns, compactions, emptyTurns: emptyTurns.length, emptyStreak: streak };
}

function main() {
  const args = process.argv.slice(2);
  const asJson = args.includes("--json");
  const id = args.find(a => !a.startsWith("--"));

  const target = id
    ? { id, log: path.join(ROOT, "--root-workspace--", `session-${id}`, "session.v4.jsonl.zstd") }
    : newestSession(ROOT);
  if (!target || !fs.existsSync(target.log)) {
    console.error("找不到会话日志"); process.exit(2);
  }

  const m = analyse(readEvents(target.log));
  const reasons = [];
  if (m.turns > TURN_LIMIT) reasons.push(`轮次 ${m.turns} > ${TURN_LIMIT}`);
  if (m.compactions >= COMPACT_LIMIT) reasons.push(`压缩 ${m.compactions} 次 ≥ ${COMPACT_LIMIT}`);
  if (m.emptyStreak >= EMPTY_STREAK_LIMIT) reasons.push(`连续 ${m.emptyStreak} 轮空回复`);

  if (asJson) {
    console.log(JSON.stringify({ session: target.id, ...m, handover: reasons.length > 0, reasons }, null, 2));
  } else {
    console.log(`会话 ${target.id.slice(0, 8)}`);
    console.log(`轮次 ${m.turns} | 压缩 ${m.compactions} | 空回合 ${m.emptyTurns} | 连续空 ${m.emptyStreak}`);
    if (reasons.length) console.log(`⚠ 应当交接：${reasons.join("；")}`);
    else console.log("✅ 健康");
  }
  process.exit(reasons.length ? 1 : 0);
}

main();

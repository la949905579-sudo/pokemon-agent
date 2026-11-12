#!/usr/bin/env node
/**
 * 会话健康检查：给交接提供客观触发依据。
 *
 * 用法：
 *   node tools/session_health.mjs                 # 检查最近活动的会话
 *   node tools/session_health.mjs <session-uuid>  # 指定会话
 *   node tools/session_health.mjs --all           # 全部会话目录（无日志的标「无数据」，不默认健康）
 *   node tools/session_health.mjs --all --json    # 机器可读
 *   node tools/session_health.mjs --help          # 用法
 *
 * 退出码：0 = 健康；1 = 命中交接阈值（应当交接）；2 = 找不到会话 / 用法错误。
 *
 * 阈值来自 docs/HANDOVER.md：
 *   - 轮次 > 100
 *   - 上下文压缩 ≥ 2 次
 *   - 最近连续 2 轮是「空回合」（无正文、无工具调用）
 *
 * A-15：会话目录可能只有 session.lock（没有 session.v4.jsonl.zstd）。
 * `--all` 必须把它们列成「无数据」，不得当成「未超线」——巡检报告要如实注明。
 */
import fs from "node:fs";
import path from "node:path";
import zlib from "node:zlib";

const ROOT = "/root/.dsh/sessions";
const TURN_LIMIT = 100;
const COMPACT_LIMIT = 2;
const EMPTY_STREAK_LIMIT = 2;

function usage() {
  const src = fs.readFileSync(new URL(import.meta.url), "utf8").split("\n");
  const start = src.findIndex(l => l.trim() === "/**") + 1;
  const end = src.findIndex((l, i) => i > start && l.trim() === "*/");
  console.log(src.slice(start, end).map(l => l.replace(/^ \* ?/, "")).join("\n"));
}

/** 列出所有会话目录；A-15：无日志的也收（hasData=false），不静默丢弃。 */
function listSessions(root) {
  const out = [];
  for (const proj of fs.readdirSync(root)) {
    const p = path.join(root, proj);
    if (!fs.statSync(p).isDirectory()) continue;
    for (const s of fs.readdirSync(p)) {
      if (!s.startsWith("session-")) continue;
      const dir = path.join(p, s);
      if (!fs.statSync(dir).isDirectory()) continue;
      const log = path.join(dir, "session.v4.jsonl.zstd");
      const hasData = fs.existsSync(log);
      const mtime = hasData ? fs.statSync(log).mtimeMs : fs.statSync(dir).mtimeMs;
      out.push({ id: s.replace("session-", ""), dir, log, hasData, mtime });
    }
  }
  out.sort((a, b) => b.mtime - a.mtime);
  return out;
}

function newestSession(root) {
  return listSessions(root).find(s => s.hasData);
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

function reasonsOf(m) {
  const reasons = [];
  if (m.turns > TURN_LIMIT) reasons.push(`轮次 ${m.turns} > ${TURN_LIMIT}`);
  if (m.compactions >= COMPACT_LIMIT) reasons.push(`压缩 ${m.compactions} 次 ≥ ${COMPACT_LIMIT}`);
  if (m.emptyStreak >= EMPTY_STREAK_LIMIT) reasons.push(`连续 ${m.emptyStreak} 轮空回复`);
  return reasons;
}

function runAll(asJson) {
  const sessions = listSessions(ROOT);
  if (!sessions.length) {
    console.error("找不到会话目录");
    return 2;
  }
  const rows = [];
  let noData = 0, handovers = 0;
  for (const s of sessions) {
    if (!s.hasData) {
      noData++;
      rows.push({ session: s.id, hasData: false, metrics: null, handover: false,
                  reasons: ["无数据（缺 session.v4.jsonl.zstd，巡检不得视为「未超线」）"] });
      continue;
    }
    let m = null, err = null;
    try { m = analyse(readEvents(s.log)); } catch (e) { err = e && e.message; }
    if (!m) {
      noData++;
      rows.push({ session: s.id, hasData: false, metrics: null, handover: false,
                  reasons: [`无数据（日志无法解析：${err || "未知错误"}）`] });
      continue;
    }
    const reasons = reasonsOf(m);
    if (reasons.length) handovers++;
    rows.push({ session: s.id, hasData: true, metrics: m, handover: reasons.length > 0, reasons });
  }

  if (asJson) {
    console.log(JSON.stringify({
      total: rows.length, withData: rows.length - noData, noData, handovers, rows,
    }, null, 2));
  } else {
    console.log(`全部会话目录：${rows.length} 个（有数据 ${rows.length - noData} / 无数据 ${noData}）`);
    for (const r of rows) {
      if (!r.hasData) {
        console.log(`session ${r.session.slice(0, 8)} | ⚪ ${r.reasons[0]}`);
        continue;
      }
      const m = r.metrics;
      console.log(`session ${r.session.slice(0, 8)} | 轮次 ${m.turns} | 压缩 ${m.compactions}`
        + ` | 空回合 ${m.emptyTurns} | 连续空 ${m.emptyStreak} | `
        + (r.handover ? `⚠ 应当交接：${r.reasons.join("；")}` : "✅ 健康"));
    }
    if (handovers) console.log(`⚠ 应当交接：${handovers} 个会话`);
    else console.log("✅ 有数据会话均未超线（无数据会话已如实标注，不参与判定）");
  }
  return handovers ? 1 : 0;
}

function main() {
  const args = process.argv.slice(2);
  const asJson = args.includes("--json");
  if (args.includes("--help") || args.includes("-h")) {
    usage();
    process.exit(0);
  }
  if (args.includes("--all")) process.exit(runAll(asJson));

  const id = args.find(a => !a.startsWith("--"));

  const target = id
    ? { id, log: path.join(ROOT, "--root-workspace--", `session-${id}`, "session.v4.jsonl.zstd") }
    : newestSession(ROOT);
  if (!target || !fs.existsSync(target.log)) {
    console.error("找不到会话日志");
    process.exit(2);
  }

  const m = analyse(readEvents(target.log));
  const reasons = reasonsOf(m);

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

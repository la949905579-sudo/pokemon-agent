#!/usr/bin/env node
/**
 * 会话 token 成本统计（只报告，不设预算红线）。
 *
 * 数据源：~/.dsh/sessions/<工作区>/<会话>/session.v4.jsonl.zstd 里的 `data.usage`
 * 字段：inputTokens / outputTokens / cacheReadTokens / cacheWriteTokens / totalTokens
 * 只输出数字与会话 id / 职位名，**不输出任何聊天内容**。
 *
 * 用法：
 *   node tools/token_report.mjs                  # 全量汇总（按职位 / 按会话 / 按天）
 *   node tools/token_report.mjs --since 2026-11-12
 *   node tools/token_report.mjs --json           # 机读 JSON
 *   node tools/token_report.mjs --write          # 写 tools/token_baseline.json（供 METRICS 引用）
 *
 * 默认输出里已含“重复读同一文件”统计，不需要额外开关。
 *
 * 职位判断：读会话里的 `subagent/descriptor.label`（考官/工匠/执行主管/督导）；
 * 没有 descriptor 的会话（主会话）标「主会话（未标注职位）」并按会话 id 单列，不猜。
 */
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import zlib from "node:zlib";

const SESSIONS_ROOT = path.join(os.homedir(), ".dsh", "sessions");
const BASELINE_PATH = path.join(import.meta.dirname, "token_baseline.json");
const TZ = "Asia/Shanghai";

const FIELDS = ["inputTokens", "outputTokens", "cacheReadTokens", "cacheWriteTokens", "totalTokens"];

function zero() {
  const o = {};
  for (const f of FIELDS) o[f] = 0;
  return o;
}

function add(a, b) {
  for (const f of FIELDS) a[f] += b[f] || 0;
  return a;
}

/** Asia/Shanghai 的本地日期 YYYY-MM-DD。 */
function localDate(ms) {
  return new Intl.DateTimeFormat("en-CA", { timeZone: TZ, year: "numeric", month: "2-digit", day: "2-digit" })
    .format(new Date(ms));
}

function roleFromLabel(label) {
  if (!label) return "主会话（未标注职位）";
  if (label.includes("考官")) return "考官";
  if (label.includes("工匠")) return "工匠";
  if (label.includes("执行主管")) return "执行主管";
  if (label.includes("督导")) return "督导";
  if (label.includes("主持")) return "主持";
  return "未知职位";
}

function sessionFiles() {
  const out = [];
  if (!fs.existsSync(SESSIONS_ROOT)) return out;
  for (const ws of fs.readdirSync(SESSIONS_ROOT)) {
    const wsDir = path.join(SESSIONS_ROOT, ws);
    if (!fs.statSync(wsDir).isDirectory()) continue;
    for (const s of fs.readdirSync(wsDir)) {
      const f = path.join(wsDir, s, "session.v4.jsonl.zstd");
      if (fs.existsSync(f)) out.push(f);
    }
  }
  return out;
}

function parseSession(file) {
  let text;
  try {
    text = zlib.zstdDecompressSync(fs.readFileSync(file)).toString("utf8");
  } catch (e) {
    return { file, error: `decode_failed code=${e.code || e.name}` };
  }
  const rec = {
    file,
    id: path.basename(path.dirname(file)),
    role: "主会话（未标注职位）",
    start: null,
    end: null,
    turns: 0,
    usageRecords: 0,
    usage: zero(),
    byDay: new Map(),
    dupReads: { extra: 0, files: new Map() },
  };
  const readCounts = new Map();
  for (const line of text.split("\n")) {
    if (!line) continue;
    let o;
    try {
      o = JSON.parse(line);
    } catch {
      continue;
    }
    if (o.type === "session" && o.id) rec.id = o.id;
    if (o.type === "subagent/descriptor" && o.data?.label) rec.role = roleFromLabel(o.data.label);
    if (typeof o.time === "number") {
      if (rec.start === null || o.time < rec.start) rec.start = o.time;
      if (rec.end === null || o.time > rec.end) rec.end = o.time;
    }
    if (o.type === "turn/start" && o.data?.turn) rec.turns = Math.max(rec.turns, o.data.turn);
    const u = o.data?.usage;
    if (u && typeof u.inputTokens === "number") {
      rec.usageRecords += 1;
      const d = zero();
      for (const f of FIELDS) d[f] = u[f] || 0;
      add(rec.usage, d);
      const day = localDate(o.time);
      if (!rec.byDay.has(day)) rec.byDay.set(day, zero());
      add(rec.byDay.get(day), d);
    }
    if (o.type === "tool/call" && o.data?.name === "read") {
      try {
        const args = JSON.parse(o.data.arguments || "{}");
        const p = args.file_path || args.path;
        if (p) readCounts.set(p, (readCounts.get(p) || 0) + 1);
      } catch {
        /* 忽略坏参数 */
      }
    }
  }
  for (const [p, n] of readCounts) {
    if (n > 1) {
      rec.dupReads.extra += n - 1;
      rec.dupReads.files.set(p, n);
    }
  }
  return rec;
}

function pct(part, whole) {
  return whole > 0 ? `${((part / whole) * 100).toFixed(1)}%` : "0%";
}

function fmt(n) {
  return n.toLocaleString("en-US");
}

function aggregate(records, since) {
  const inWindow = (ms) => since === null || localDate(ms) >= since;
  const sessions = [];
  const byRole = new Map();
  const byDay = new Map();
  const dupFiles = new Map();
  let totals = zero();
  let usageRecords = 0;

  for (const rec of records) {
    if (rec.error) continue;
    // 按天裁剪（--since）：只算窗口内的 usage
    const usage = zero();
    let kept = 0;
    for (const [day, d] of rec.byDay) {
      if (since !== null && day < since) continue;
      add(usage, d);
      if (!byDay.has(day)) byDay.set(day, zero());
      add(byDay.get(day), d);
      kept += 1;
    }
    if (kept === 0) continue;
    const role = byRole.get(rec.role) || { role: rec.role, sessions: 0, ...zero() };
    role.sessions += 1;
    add(role, usage);
    byRole.set(rec.role, role);
    add(totals, usage);
    usageRecords += 1;
    sessions.push({
      id: rec.id,
      role: rec.role,
      start: rec.start,
      end: rec.end,
      turns: rec.turns,
      usage,
      dupReads: rec.dupReads.extra,
    });
    for (const [p, n] of rec.dupReads.files) dupFiles.set(p, (dupFiles.get(p) || 0) + (n - 1));
  }

  sessions.sort((a, b) => b.usage.totalTokens - a.usage.totalTokens);
  const roles = [...byRole.values()].sort((a, b) => b.totalTokens - a.totalTokens);
  const days = [...byDay.entries()].sort((a, b) => (a[0] < b[0] ? -1 : 1)).map(([day, u]) => ({ day, ...u }));
  const dup = {
    extra: [...dupFiles.values()].reduce((x, y) => x + y, 0),
    top: [...dupFiles.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([file, extra]) => ({ file, extra })),
  };
  return { since, generatedAt: new Date().toISOString(), sessions, roles, days, totals, dup, usageRecords };
}

function printHuman(agg) {
  const { totals, roles, sessions, days, dup } = agg;
  console.log(`token 成本基线（只报告）  窗口：${agg.since ? `>= ${agg.since}` : "全部"}  ${agg.generatedAt}`);
  console.log(
    `合计：input ${fmt(totals.inputTokens)} / output ${fmt(totals.outputTokens)} / cacheRead ${fmt(totals.cacheReadTokens)} / total ${fmt(totals.totalTokens)}（${agg.usageRecords} 个会话）`,
  );
  console.log("\n按职位：");
  console.log("职位\t会话\tinput\toutput\tcacheRead\ttotal\ttotal占比");
  for (const r of roles) {
    console.log(
      `${r.role}\t${r.sessions}\t${fmt(r.inputTokens)}\t${fmt(r.outputTokens)}\t${fmt(r.cacheReadTokens)}\t${fmt(r.totalTokens)}\t${pct(r.totalTokens, totals.totalTokens)}`,
    );
  }
  console.log("\n按会话（total 降序）：");
  console.log("会话\t职位\t轮次\ttotal\tinput\toutput\tcacheRead");
  for (const s of sessions) {
    console.log(`${s.id.slice(0, 16)}\t${s.role}\t${s.turns}\t${fmt(s.usage.totalTokens)}\t${fmt(s.usage.inputTokens)}\t${fmt(s.usage.outputTokens)}\t${fmt(s.usage.cacheReadTokens)}`);
  }
  console.log("\n按天：");
  console.log("日期\ttotal\tinput\toutput\tcacheRead");
  for (const d of days) console.log(`${d.day}\t${fmt(d.totalTokens)}\t${fmt(d.inputTokens)}\t${fmt(d.outputTokens)}\t${fmt(d.cacheReadTokens)}`);
  console.log(`\n重复读同一文件：额外读 ${dup.extra} 次`);
  for (const f of dup.top) console.log(`  ${f.extra} 次重复读  ${f.file}`);
}

function main() {
  const args = process.argv.slice(2);
  const sinceIdx = args.indexOf("--since");
  const since = sinceIdx >= 0 ? args[sinceIdx + 1] : null;
  if (since && !/^\d{4}-\d{2}-\d{2}$/.test(since)) {
    console.error("--since 需要 YYYY-MM-DD");
    return 2;
  }
  const files = sessionFiles();
  if (files.length === 0) {
    console.error(`没有找到会话日志：${SESSIONS_ROOT}`);
    return 1;
  }
  const records = files.map(parseSession);
  const agg = aggregate(records, since);

  if (args.includes("--json")) {
    console.log(JSON.stringify(agg, null, 2));
  } else {
    printHuman(agg);
  }

  if (args.includes("--write")) {
    const baseline = {
      generatedAt: agg.generatedAt,
      windowSince: since,
      totals: agg.totals,
      sessionsCount: agg.usageRecords,
      byRole: agg.roles,
      bySession: agg.sessions.map((s) => ({
        id: s.id,
        role: s.role,
        turns: s.turns,
        start: s.start,
        end: s.end,
        ...s.usage,
      })),
      byDay: agg.days,
      dupReads: agg.dup,
      source: "~/.dsh/sessions/*/*/session.v4.jsonl.zstd（data.usage），无聊天内容",
    };
    fs.writeFileSync(BASELINE_PATH, JSON.stringify(baseline, null, 2) + "\n");
    console.log(`\n已写入 ${path.relative(process.cwd(), BASELINE_PATH)}`);
  }
  return 0;
}

process.exit(main());

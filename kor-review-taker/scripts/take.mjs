#!/usr/bin/env node
// kor-review-taker 실행기. 상품 URL → 플랫폼 판별 → bsk 세션에서 상품 페이지 열기 → 수집기를 같은 탭에서 실행
// → 결과 검증 → CSV·JSON 저장. 사용법은 `node take.mjs --help`.
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const COLLECTORS = path.join(HERE, "collectors");
const BSK =
  process.env.BSK_BIN ||
  [path.join(os.homedir(), ".local/bin/bsk"), "bsk"].find(
    (p) => p === "bsk" || fs.existsSync(p),
  );

// 종료 코드 — SKILL.md 의 판단표와 같다.
const EXIT = {
  OK: 0,
  PARTIAL: 2,
  STRUCTURE: 3,
  UNSUPPORTED: 4,
  BLOCKED: 5,
  LOGIN_REQUIRED: 6,
  COOLDOWN: 7,
  NAVIGATED: 8,
  USAGE: 64,
};

// minDelayMs — 페이지 간 최소 간격(--delay-ms 가 더 크면 그쪽). cooldownMin — 같은 브라우저로 다시 열기 전 대기.
// 쿠팡은 같은 브라우저로 하루 여러 번 열면 페이지째 막는다(2026-10-21 실측). G마켓은 1초 안팎 간격에서 리뷰만 막혔다.
const PLATFORMS = [
  {
    id: "coupang",
    test: /(^|\.)coupang\.com$/,
    minDelayMs: 3000,
    cooldownMin: 30,
  },
  {
    id: "naver",
    test: /^(smartstore|brand|m\.smartstore|m\.brand)\.naver\.com$/,
  },
  { id: "11st", test: /(^|\.)11st\.co\.kr$/ },
  { id: "gmarket", test: /^item\.gmarket\.co\.kr$/, minDelayMs: 2000 },
  { id: "himart", test: /(^|\.)e-himart\.co\.kr$/ },
  { id: "ssg", test: /(^|\.)ssg\.com$/ },
  { id: "lotteon", test: /(^|\.)lotteon\.com$/ },
];

const HELP = `kor-review-taker — 국내 이커머스 상품 리뷰를 CSV 로 내려받는다

  node take.mjs <상품URL> [<상품URL>...] [옵션]

옵션
  --browser <id|label>   bsk 브라우저 인스턴스 (브라우저가 둘 이상이면 필수)
  --out <dir>            저장 폴더 (기본 ~/Downloads/kor-reviews/<YYYYMMDD>)
  --max-pages <n>        상품당 최대 페이지 (기본 100)
  --delay-ms <n>         페이지 간 기본 간격 (기본 1200, 무작위 +30%. 쿠팡 최소 3000·G마켓 최소 2000)
  --ignore-cooldown      재실행 대기(쿠팡 30분)를 무시하고 연다
  --collector <file>     수집기 파일을 직접 지정 (구조 수정 시험용)
  --platforms            지원 플랫폼과 수집기 파일 목록

종료 코드  0 OK · 2 PARTIAL · 3 STRUCTURE · 4 UNSUPPORTED · 5 BLOCKED · 6 LOGIN_REQUIRED · 7 COOLDOWN · 8 NAVIGATED · 64 사용법 오류
결과       <out>/<platform>_<product>.csv · .json, 여러 개면 merged.csv, 항상 run-report.json`;

function parseArgs(argv) {
  const a = { urls: [], maxPages: 100, delayMs: 1200 };
  for (let i = 0; i < argv.length; i++) {
    const k = argv[i];
    const v = () => argv[++i];
    if (k === "--help" || k === "-h") a.help = true;
    else if (k === "--browser") a.browser = v();
    else if (k === "--out") a.out = v();
    else if (k === "--max-pages") a.maxPages = +v();
    else if (k === "--delay-ms") a.delayMs = +v();
    else if (k === "--collector") a.collector = v();
    else if (k === "--ignore-cooldown") a.ignoreCooldown = true;
    else if (k === "--platforms") a.listPlatforms = true;
    else if (k.startsWith("--")) throw usage(`알 수 없는 옵션 ${k}`);
    else a.urls.push(k);
  }
  return a;
}

function usage(msg) {
  const e = new Error(msg);
  e.code = EXIT.USAGE;
  return e;
}

function bsk(args, { json = true, timeoutMs = 120000 } = {}) {
  const out = execFileSync(BSK, args, {
    encoding: "utf8",
    timeout: timeoutMs,
    maxBuffer: 256 * 1024 * 1024,
    stdio: ["ignore", "pipe", "pipe"],
  });
  return json ? JSON.parse(out) : out;
}

function bskSafe(args, opts) {
  try {
    return { ok: true, value: bsk(args, opts) };
  } catch (e) {
    const raw = String(e.stdout || "") + String(e.stderr || "");
    let parsed = null;
    try {
      parsed = JSON.parse(e.stdout);
    } catch {}
    return {
      ok: false,
      error: parsed?.message || raw.trim() || e.message,
      code: parsed?.code,
    };
  }
}

// 페이지가 스스로 다시 이동하는 동안 evaluate 하면 CDP 가 이 오류로 끊는다(쿠팡 2026-10-22·23 실측). 구조 변경이 아니다.
const NAVIGATED_RE =
  /Inspected target navigated or closed|Execution context was destroyed|Cannot find context with specified id/i;

function classifyEvalError(msg) {
  if (/BLOCKED|Failed to fetch/.test(msg)) return "BLOCKED";
  if (NAVIGATED_RE.test(msg)) return "NAVIGATED";
  return "STRUCTURE";
}

// probe() 는 "주소|readyState" 또는 null(이동 중이라 못 읽음). 같은 값이 stableMs 동안 이어지고 complete 면 멈춘 것.
async function waitSettled(
  probe,
  {
    timeoutMs = 15000,
    stableMs = 2000,
    pollMs = 500,
    now = Date.now,
    sleep = (ms) => new Promise((r) => setTimeout(r, ms)),
  } = {},
) {
  const end = now() + timeoutMs;
  let last = null;
  let since = now();
  while (now() < end) {
    const s = probe();
    if (s !== last) [last, since] = [s, now()];
    else if (s?.endsWith("|complete") && now() - since >= stableMs) return true;
    await sleep(pollMs);
  }
  return false;
}

// 수집기가 페이지 이동으로 끊겼으면 같은 탭에서 멈추길 기다렸다가 한 번만 다시 돌린다.
// 새로 열지 않는다 — 쿠팡은 방문 횟수로 막는다. 기다리는 동안 차단·로그인 화면으로 바뀌었으면 그 상태로 끝낸다.
async function collect({ evaluate, settle, gate }) {
  const first = evaluate();
  if (first.status !== "NAVIGATED") return first;
  await settle();
  const stop = gate();
  if (stop) return { ...stop, retried: true };
  return { ...evaluate(), retried: true };
}

function platformOf(u) {
  const host = new URL(u).hostname;
  return PLATFORMS.find((p) => p.test.test(host))?.id || null;
}

// 플랫폼@브라우저 마다 마지막으로 페이지를 연 시각. 차단 여부와 상관없이 연 순간 기록한다(사이트는 방문으로 센다).
const VISITS = path.join(os.homedir(), ".cache/kor-review-taker/visits.json");

function readVisits() {
  try {
    return JSON.parse(fs.readFileSync(VISITS, "utf8"));
  } catch {
    return {};
  }
}

function recordVisit(key) {
  const v = readVisits();
  v[key] = new Date().toISOString();
  fs.mkdirSync(path.dirname(VISITS), { recursive: true });
  fs.writeFileSync(VISITS, JSON.stringify(v, null, 2));
}

// 수집기 파일 = 함수 식 하나. 공통 헬퍼와 묶어 `(async () => { 헬퍼; return await (수집기)(opts) })()` 로 만든다.
function buildExpression(collectorFile, opts) {
  const common = fs.readFileSync(path.join(COLLECTORS, "_common.js"), "utf8");
  const fn = fs.readFileSync(collectorFile, "utf8").trim().replace(/;\s*$/, "");
  return `(async () => {\n${common}\nreturn await (\n${fn}\n)(${JSON.stringify(opts)});\n})()`;
}

// '2026.09.24' 같은 점 구분 날짜만 하이픈으로 바꾼다. ISO 시각의 밀리초 점은 건드리지 않는다.
const normDate = (v) =>
  String(v ?? "")
    .trim()
    .replace(/^(\d{4})\.(\d{1,2})\.(\d{1,2})\.?/, "$1-$2-$3");

// 결과가 쓸 만한지 결정론적으로 판단한다. 여기서 STRUCTURE 가 나오면 SKILL.md 의 자가 복구 절차로 간다.
// 화면 건수를 못 읽었는데 0건이면 OK 로 넘기지 않는다 — 엉뚱한 엔드포인트를 읽은 경우가 이렇게 보였다(11번가 실측).
function judge(r) {
  const n = r.reviews.length;
  const exp = r.expected_total;
  if (exp === 0) return { status: "OK", note: "리뷰 0건(화면 건수 0)" };
  if (exp == null && n === 0)
    return {
      status: "STRUCTURE",
      note: "0건인데 화면 건수를 확인하지 못함 — 화면에서 리뷰 수를 확인",
    };
  if (n === 0)
    return { status: "STRUCTURE", note: `화면 건수 ${exp} 인데 0건 수집` };
  const filled = r.reviews.filter(
    (x) => (x.content && String(x.content).trim()) || x.rating !== "",
  ).length;
  const dated = r.reviews.filter(
    (x) => x.created_at && !Number.isNaN(Date.parse(normDate(x.created_at))),
  ).length;
  if (filled / n < 0.8)
    return {
      status: "STRUCTURE",
      note: `본문·별점이 빈 항목 ${n - filled}/${n}`,
    };
  if (dated / n < 0.8)
    return {
      status: "STRUCTURE",
      note: `작성일을 못 읽은 항목 ${n - dated}/${n}`,
    };
  if (exp != null && n < exp * 0.95)
    return { status: "PARTIAL", note: `${n}/${exp} 건` };
  return {
    status: "OK",
    note: exp != null ? `${n}/${exp} 건` : `${n} 건(화면 건수 미확인)`,
  };
}

const COLS = [
  "platform",
  "product_id",
  "product_name",
  "review_id",
  "created_at",
  "rating",
  "writer",
  "option",
  "title",
  "content",
  "content_length",
  "survey",
  "helpful",
  "photo_count",
  "photo_urls",
  "product_url",
  "collected_at",
];

function toRows(r, url, collectedAt) {
  return r.reviews.map((x) => {
    const c = String(x.content ?? "");
    const d = normDate(x.created_at);
    const t = Date.parse(d);
    return {
      ...x,
      platform: r.platform,
      product_id: r.product_id,
      product_name: r.product_name,
      created_at: Number.isNaN(t)
        ? d
        : new Date(t + 9 * 3600e3).toISOString().slice(0, 10),
      content_length: c.length,
      product_url: url,
      collected_at: collectedAt,
    };
  });
}

function writeCsv(file, rows) {
  const esc = (v) =>
    `"${String(v ?? "")
      .replace(/\s+/g, " ")
      .trim()
      .replace(/"/g, '""')}"`;
  const lines = [
    COLS.join(","),
    ...rows.map((r) => COLS.map((c) => esc(r[c])).join(",")),
  ];
  fs.writeFileSync(file, "﻿" + lines.join("\r\n") + "\r\n");
}

// 로그인·차단 화면이면 그 상태를, 아니면 null.
function pageGate(sid, platform) {
  // 일반 스마트스토어 상품은 로그아웃 상태에서 네이버 로그인으로 넘어간다(2026-10-22 실측, 브랜드스토어는 열림).
  const here =
    bskSafe(["evaluate", "--session", sid, "--json", "location.href"]).value
      ?.value || "";
  if (
    /nid\.naver\.com|login\.coupang\.com|\/(login|signin)([/?#]|$)/i.test(
      here,
    )
  ) {
    console.error(`✗ LOGIN_REQUIRED ${platform} — ${here.split("?")[0]}`);
    return {
      status: "LOGIN_REQUIRED",
      note: `로그인 페이지로 이동함: ${here.split("?")[0]}`,
    };
  }
  // 쿠팡 차단 페이지는 제목이 "쿠팡!" 이라 본문 문구까지 본다.
  const head =
    bskSafe([
      "evaluate",
      "--session",
      sid,
      "--json",
      "document.title + ' ' + (document.body?.innerText || '').slice(0, 600)",
    ]).value?.value || "";
  if (
    /access denied|captcha|보안문자|robot|사용권한이 (없|제한)|비정상적인 (접근|트래픽)|접근이 (차단|제한)/i.test(
      head,
    )
  ) {
    console.error(`✗ BLOCKED ${platform} — 차단 페이지`);
    return {
      status: "BLOCKED",
      note: `차단 페이지: ${head.replace(/\s+/g, " ").slice(0, 120)}`,
    };
  }
  return null;
}

async function main() {
  const a = parseArgs(process.argv.slice(2));
  if (a.help) return (console.log(HELP), EXIT.OK);
  if (a.listPlatforms) {
    for (const p of PLATFORMS)
      console.log(`${p.id.padEnd(8)} ${p.test}  collectors/${p.id}.js`);
    return EXIT.OK;
  }
  if (!a.urls.length) throw usage("상품 URL 이 필요하다 (--help)");
  if (!BSK)
    throw usage("bsk CLI 를 찾지 못했다 — browser-skill 설치가 필요하다");

  const today = new Date(Date.now() + 9 * 3600e3)
    .toISOString()
    .slice(0, 10)
    .replace(/-/g, "");
  const out = path.resolve(
    (a.out || path.join(os.homedir(), "Downloads/kor-reviews", today)).replace(
      /^~(?=\/)/,
      os.homedir(),
    ),
  );
  fs.mkdirSync(out, { recursive: true });

  const report = { started_at: new Date().toISOString(), out, results: [] };
  const merged = [];
  const start = bskSafe([
    "session",
    "start",
    "--no-focus",
    "--json",
    ...(a.browser ? ["--browser", a.browser] : []),
  ]);
  if (!start.ok) {
    console.error(`세션 시작 실패: ${start.error}`);
    if (start.code === "multiple_browsers_online")
      console.error("→ bsk browsers 로 확인하고 --browser <id> 를 넘긴다");
    return EXIT.USAGE;
  }
  const sid = start.value.session_id;
  const browserId = start.value.browser_instance_id;
  console.error(`session ${sid} (browser ${browserId})`);

  try {
    for (const url of a.urls) {
      const platform = platformOf(url);
      const res = { url, platform };
      report.results.push(res);
      const file = a.collector
        ? path.resolve(a.collector)
        : platform && path.join(COLLECTORS, `${platform}.js`);
      if (!file || !fs.existsSync(file)) {
        Object.assign(res, {
          status: "UNSUPPORTED",
          note: `수집기 없음 (${new URL(url).hostname})`,
        });
        console.error(`✗ UNSUPPORTED ${url}`);
        continue;
      }
      const spec = PLATFORMS.find((p) => p.id === platform) || {};
      const visitKey = `${platform}@${browserId}`;
      const last = Date.parse(readVisits()[visitKey] || "");
      const waitMin = spec.cooldownMin
        ? Math.ceil(spec.cooldownMin - (Date.now() - last) / 60000)
        : 0;
      if (waitMin > 0 && !a.ignoreCooldown) {
        Object.assign(res, {
          status: "COOLDOWN",
          note: `같은 브라우저로 ${spec.cooldownMin - waitMin}분 전에 열었음 — ${waitMin}분 뒤 다시(--ignore-cooldown 으로 무시)`,
        });
        console.error(`✗ COOLDOWN ${platform} — ${waitMin}분 남음`);
        continue;
      }
      recordVisit(visitKey);
      const nav = bskSafe(["navigate", url, "--session", sid], {
        json: false,
        timeoutMs: 120000,
      });
      if (!nav.ok) {
        Object.assign(res, {
          status: "BLOCKED",
          note: `페이지 열기 실패: ${nav.error.slice(0, 200)}`,
        });
        continue;
      }
      const probe = () =>
        bskSafe([
          "evaluate",
          "--session",
          sid,
          "--json",
          "location.href + '|' + document.readyState",
        ]).value?.value ?? null;
      const settle = () => waitSettled(probe);
      const gate = () => pageGate(sid, platform);
      await settle();
      const stop = gate();
      if (stop) {
        Object.assign(res, stop);
        continue;
      }
      const opts = {
        maxPages: a.maxPages,
        delayMs: Math.max(a.delayMs, spec.minDelayMs || 0),
      };
      const timeout = `${Math.min(30, Math.ceil((a.maxPages * (opts.delayMs * 1.3 + 1500)) / 60000) + 2)}m`;
      const runCollector = () => {
        const ev = bskSafe(
          [
            "evaluate",
            "--session",
            sid,
            "--json",
            "--timeout",
            timeout,
            buildExpression(file, opts),
          ],
          { timeoutMs: 31 * 60000 },
        );
        const v = ev.ok ? ev.value : null;
        if (v?.ok) return { ok: true, value: v.value };
        const msg = v?.error?.text || ev.error || "evaluate 실패";
        return { status: classifyEvalError(msg), msg };
      };
      const got = await collect({ evaluate: runCollector, settle, gate });
      if (!got.ok) {
        const where = (probe() || "").split("|")[0].split("?")[0];
        const note =
          got.status === "NAVIGATED"
            ? `수집 중 페이지가 다시 이동함(같은 탭 재시도 1회 포함), 마지막 주소 ${where}`
            : got.msg
              ? got.msg.split("\n")[0].slice(0, 300)
              : got.note;
        Object.assign(res, {
          status: got.status,
          note,
          retried: !!got.retried,
          collector: path.relative(HERE, file),
        });
        console.error(`✗ ${got.status} ${platform} — ${note}`);
        continue;
      }
      const r = got.value;
      const j = judge(r);
      const base = `${r.platform}_${String(r.product_id).replace(/[^\w-]/g, "")}`;
      const rows = toRows(r, url, report.started_at);
      fs.writeFileSync(
        path.join(out, `${base}.json`),
        JSON.stringify({ ...r, url, judged: j }, null, 2),
      );
      writeCsv(path.join(out, `${base}.csv`), rows);
      merged.push(...rows);
      Object.assign(res, {
        ...j,
        product_id: r.product_id,
        product_name: r.product_name,
        collected: r.reviews.length,
        expected_total: r.expected_total,
        pages: r.log,
        csv: path.join(out, `${base}.csv`),
        collector: path.relative(HERE, file),
      });
      console.error(
        `${j.status === "OK" ? "✓" : "✗"} ${j.status} ${platform} ${r.product_id} — ${j.note} [${r.log}]`,
      );
    }
  } finally {
    bskSafe(["session", "stop", sid], { json: false });
  }

  if (a.urls.length > 1 && merged.length)
    writeCsv(path.join(out, "merged.csv"), merged);
  report.finished_at = new Date().toISOString();
  fs.writeFileSync(
    path.join(out, "run-report.json"),
    JSON.stringify(report, null, 2),
  );
  console.log(JSON.stringify(report, null, 2));

  const worst = Math.max(
    ...report.results.map((r) => EXIT[r.status] ?? EXIT.STRUCTURE),
  );
  return worst;
}

export { EXIT, classifyEvalError, waitSettled, collect };

// 시험에서 import 할 때는 돌지 않는다. 링크 경로(/tmp → /private/tmp 등)로 실행해도 돌도록 실제 경로로 비교한다.
const invokedDirectly = () => {
  try {
    return fs.realpathSync(process.argv[1]) === fs.realpathSync(fileURLToPath(import.meta.url));
  } catch {
    return false;
  }
};
if (process.argv[1] && invokedDirectly())
  main().then(
    (code) => process.exit(code),
    (e) => {
      console.error(e.message);
      process.exit(e.code || 1);
    },
  );

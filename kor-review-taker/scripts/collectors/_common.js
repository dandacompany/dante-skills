// 모든 수집기 앞에 붙는 브라우저 안 공통 헬퍼. take.mjs 가 이 파일과 수집기를 하나의 식으로 묶어
// `bsk evaluate` 로 상품 페이지 탭에서 실행한다. 같은 출처 fetch 라서 쿠키·봇 쿠키가 자연히 붙는다.
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const jitter = (ms) => ms + Math.floor(Math.random() * ms * 0.3);
const html = (t) => new DOMParser().parseFromString(t, "text/html");
const txt = (el) =>
  (el?.innerText || el?.textContent || "").replace(/\s+/g, " ").trim();

// 네트워크 오류·429·5xx 는 물러났다가 재시도한다. 세 번 실패하면 BLOCKED 로 던진다.
async function req(url, init = {}, kind = "text") {
  let last;
  for (let i = 0; i < 3; i++) {
    try {
      const r = await fetch(url, { credentials: "include", ...init });
      if (r.status === 429 || r.status >= 500)
        throw new Error("HTTP " + r.status);
      // 401/403 은 봇 차단인 경우가 대부분이다(쿠팡 실측). 구조 문제로 오인해 수집기를 고치지 않게 BLOCKED 로 낸다.
      if (r.status === 401 || r.status === 403)
        throw new Error("BLOCKED: HTTP " + r.status + " " + url.split("?")[0]);
      if (r.status >= 400)
        throw new Error(
          "STRUCTURE: HTTP " + r.status + " " + url.split("?")[0],
        );
      return kind === "json" ? await r.json() : await r.text();
    } catch (e) {
      if (/^(STRUCTURE|BLOCKED)/.test(String(e.message))) throw e;
      last = e;
      await sleep(8000 * (i + 1));
    }
  }
  throw new Error("BLOCKED: " + url.split("?")[0] + " — " + last.message);
}

// fetchPage(p) → { items, total? }. 빈 페이지는 소프트 스로틀링일 수 있어 기다렸다 두 번 더 본다
// (SSG 실측: 연속 요청 중 빈 응답이 섞이고 4초 뒤 정상). 전체 건수에 닿거나 새 항목이 없으면 멈춘다.
async function paginate(fetchPage, { maxPages, delayMs }) {
  const seen = new Map();
  const log = [];
  let expected = null;
  for (let p = 1; p <= maxPages; p++) {
    let { items, total } = await fetchPage(p);
    if (total != null) expected = total;
    let retry = 0;
    while (
      !items.length &&
      retry < 2 &&
      (expected == null || seen.size < expected)
    ) {
      retry++;
      await sleep(4000 * retry);
      ({ items } = await fetchPage(p));
    }
    let added = 0;
    for (const it of items) {
      const k = String(
        it.review_id ||
          [it.writer, it.created_at, (it.content || "").slice(0, 60)].join("|"),
      );
      if (!seen.has(k)) {
        seen.set(k, it);
        added++;
      }
    }
    log.push(`${p}:${items.length}${retry ? "r" + retry : ""}`);
    if (!added || (expected != null && seen.size >= expected)) break;
    await sleep(jitter(delayMs));
  }
  return {
    expected_total: expected,
    reviews: [...seen.values()],
    log: log.join(" "),
  };
}

// 리뷰 영역이 화면에 들어와야 요청을 보내는 사이트가 있어(네이버) 조금씩 내려 보며 조건을 기다린다.
async function scrollUntil(check, tries = 12) {
  for (let i = 0; i < tries; i++) {
    const v = check();
    if (v) return v;
    window.scrollBy(0, 1400);
    await sleep(900);
  }
  return check();
}

// 같은 출처 iframe 까지 포함한 XHR/fetch 리소스 URL 목록. 11번가처럼 iframe 안에서 부르는 경우용.
function resourceUrls() {
  const wins = [window];
  for (const f of document.querySelectorAll("iframe")) {
    try {
      if (f.contentWindow.document) wins.push(f.contentWindow);
    } catch {}
  }
  return wins.flatMap((w) =>
    w.performance
      .getEntriesByType("resource")
      .filter((e) => /xmlhttprequest|fetch/.test(e.initiatorType))
      .map((e) => e.name),
  );
}

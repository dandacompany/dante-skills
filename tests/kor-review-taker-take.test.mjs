// node --test tests/ — take.mjs 의 판정·대기·재시도 (브라우저 없이)
import assert from "node:assert/strict";
import test from "node:test";
import {
  EXIT,
  classifyEvalError,
  collect,
  waitSettled,
} from "../kor-review-taker/scripts/take.mjs";

const CDP = '{"code":-32000,"message":"Inspected target navigated or closed"}';

test("page navigation is NAVIGATED, not STRUCTURE", () => {
  assert.equal(classifyEvalError(CDP), "NAVIGATED");
  assert.equal(
    classifyEvalError(
      "Execution context was destroyed, most likely because of a navigation",
    ),
    "NAVIGATED",
  );
  assert.equal(classifyEvalError("BLOCKED: 403"), "BLOCKED");
  assert.equal(classifyEvalError("TypeError: Failed to fetch"), "BLOCKED");
  assert.equal(classifyEvalError("STRUCTURE: rData.paging 없음"), "STRUCTURE");
  assert.equal(EXIT.NAVIGATED, 8);
});

function clock() {
  let t = 0;
  return { now: () => t, sleep: async (ms) => void (t += ms) };
}

test("waitSettled waits until the address stops changing and the page is complete", async () => {
  const c = clock();
  // 1초 뒤 같은 상품으로 다시 이동하는 쿠팡처럼: 이동 중(null) → 새 주소 loading → complete
  const seq = ["a|complete", null, "a?x|loading", "a?x|complete"];
  const probe = () => seq[Math.min(Math.floor(c.now() / 500), seq.length - 1)];
  assert.equal(await waitSettled(probe, c), true);
  assert.ok(c.now() >= 1500 + 2000, `settled too early at ${c.now()}`);
});

test("waitSettled gives up after the timeout when the page keeps moving", async () => {
  const c = clock();
  const probe = () => `p${c.now()}|loading`;
  assert.equal(await waitSettled(probe, { ...c, timeoutMs: 5000 }), false);
  assert.ok(c.now() >= 5000 && c.now() < 6000);
});

function harness(results, gateResult = null) {
  const calls = [];
  return {
    calls,
    evaluate: () => (calls.push("eval"), results.shift()),
    settle: async () => void calls.push("settle"),
    gate: () => (calls.push("gate"), gateResult),
  };
}

test("collect retries once in the same tab after a navigation", async () => {
  const h = harness([
    { status: "NAVIGATED", msg: CDP },
    { ok: true, value: 1 },
  ]);
  assert.deepEqual(await collect(h), { ok: true, value: 1, retried: true });
  assert.deepEqual(h.calls, ["eval", "settle", "gate", "eval"]);
});

test("collect reports NAVIGATED when the retry is cut off too", async () => {
  const h = harness([
    { status: "NAVIGATED", msg: CDP },
    { status: "NAVIGATED", msg: CDP },
  ]);
  assert.equal((await collect(h)).status, "NAVIGATED");
  assert.equal(h.calls.filter((c) => c === "eval").length, 2);
});

test("collect stops without retrying when the page turned into a block page", async () => {
  const h = harness([{ status: "NAVIGATED", msg: CDP }], {
    status: "BLOCKED",
    note: "차단 페이지: 쿠팡!",
  });
  assert.deepEqual(await collect(h), {
    status: "BLOCKED",
    note: "차단 페이지: 쿠팡!",
    retried: true,
  });
  assert.deepEqual(h.calls, ["eval", "settle", "gate"]);
});

test("collect does not retry other failures", async () => {
  for (const status of ["STRUCTURE", "BLOCKED"]) {
    const h = harness([{ status, msg: "x" }]);
    assert.equal((await collect(h)).status, status);
    assert.deepEqual(h.calls, ["eval"]);
  }
});

// G마켓 — POST /Review/Text(일반 상품평)·/Review/Premium(포토 상품평), form-urlencoded, HTML 조각.
// 부분 검증: 일반 상품평 1/1(2026-10-21), 두 엔드포인트의 페이지 파라미터는 화면 클릭으로 확인(2026-10-22).
// 800건대 전체 수집 시도 중 리뷰 엔드포인트가 'Failed to fetch' 로 막혔다 — 간격을 넉넉히(기본 2초) 둔다.
async (opts) => {
  const goodsCode =
    new URLSearchParams(location.search).get("goodscode") ||
    new URLSearchParams(location.search).get("goodsCode");
  if (!goodsCode) throw new Error("STRUCTURE: goodscode 를 URL 에서 찾지 못함");
  const seller = (document.documentElement.innerHTML.match(
    /sellerCustNo['"]?\s*[:=]\s*['"]?(\d+)/,
  ) || [])[1];
  if (!seller)
    throw new Error("STRUCTURE: sellerCustNo 를 페이지에서 찾지 못함");
  const post = (path, body) =>
    req(path, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
      },
      body,
    }).then(html);
  const parse = (d, kind) =>
    [...d.querySelectorAll("table tbody tr")]
      .map((tr) => txt(tr))
      .filter((t) => /작성자\s*:/.test(t))
      .map((t) => {
        const writer = (t.match(/작성자\s*:\s*(\S+)/) || [])[1] || "";
        const date = (t.match(/등록일\s*:\s*([\d.]+)/) || [])[1] || "";
        const body = t.replace(/작성자\s*:.*$/, "").trim();
        const m =
          kind === "text" ? body.match(/^(\S+)\s+(\S+)\s+(\S+)\s+(.*)$/) : null;
        return {
          review_id: "",
          created_at: date.replace(/\./g, "-"),
          rating: "",
          writer,
          option: m ? m[3] : "",
          title: "",
          content: m ? m[4] : body,
          survey: m ? `추천: ${m[1]} / 배송: ${m[2]}` : "",
          helpful: "",
          photo_count: kind === "photo" ? 1 : 0,
          photo_urls: "",
          kind,
        };
      });
  const first = await post(
    "/Review",
    `goodsCode=${goodsCode}&sellerCustNo=${seller}`,
  );
  const out = { reviews: [], log: [], expected_total: null };
  for (const [kind, path, extra] of [
    ["text", "/Review/Text", ""],
    ["photo", "/Review/Premium", "&sort=0"],
  ]) {
    const r = await paginate(
      async (p) => {
        const d =
          p === 1 && kind === "text"
            ? first
            : await post(
                path,
                `goodsCode=${goodsCode}&pageNo=${p}${extra}&sellerCustNo=${seller}`,
              );
        return { items: parse(d, kind) };
      },
      { ...opts, delayMs: Math.max(opts.delayMs, 2000) },
    );
    out.reviews.push(...r.reviews);
    out.log.push(`${kind}[${r.log}]`);
  }
  return {
    platform: "gmarket",
    product_id: goodsCode,
    product_name: document.title.replace(/^G마켓\s*-\s*/, ""),
    ...out,
    log: out.log.join(" "),
  };
};

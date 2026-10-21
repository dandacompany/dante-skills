// 쿠팡 — GET /next-api/review (JSON). 로그인 불필요. 2026-10-21 실측 83/83.
async (opts) => {
  const pid = location.pathname.match(/\/vp\/products\/(\d+)/)?.[1];
  if (!pid) throw new Error("STRUCTURE: productId 를 URL 에서 찾지 못함");
  // 상품평 영역을 띄워 페이지가 스스로 리뷰를 한 번 부르게 둔다(처음 성공한 흐름과 같게). 못 봐도 계속 진행한다.
  await scrollUntil(
    () => resourceUrls().some((u) => /\/next-api\/review\?/.test(u)),
    8,
  );
  const res = await paginate(async (p) => {
    const j = await req(
      `/next-api/review?productId=${pid}&page=${p}&size=10&sortBy=DATE_DESC&ratingSummary=true&ratings=&market=`,
      { headers: { Accept: "application/json, text/plain, */*" } },
      "json",
    );
    const pg = j?.rData?.paging;
    if (j?.rCode !== "RET0000" || !Array.isArray(pg?.contents))
      throw new Error("STRUCTURE: rCode/rData.paging.contents 없음");
    return {
      total: pg.totalCount,
      items: pg.contents.map((c) => ({
        review_id: c.reviewId,
        created_at: new Date(c.reviewAt).toISOString(),
        rating: c.rating,
        writer: c.displayName,
        option: c.itemName,
        title: c.title,
        content: c.content,
        survey: (c.reviewSurveyAnswers || [])
          .map((a) => `${a.question}: ${a.answer}`)
          .join(" / "),
        helpful: c.helpfulTrueCount,
        photo_count: (c.attachments || []).length,
        photo_urls: (c.attachments || []).map((a) => a.imgSrcOrigin).join(" "),
      })),
    };
  }, opts);
  return {
    platform: "coupang",
    product_id: pid,
    product_name: document.title.replace(/\s*[-|]\s*[^-|]*쿠팡\s*$/, ""),
    ...res,
  };
};
